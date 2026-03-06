import os
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.api.routes import _get_doc, _load_script
from app.models.schemas import ScriptResponse
from app.models.video_schemas import SceneResponse, ProjectMetadata, AssetGenerationRequest, SceneStatus, AssetStatus
from app.video.scene_segmentation import segmenter
from app.video.project_manager import ProjectMetadataManager, TimelineService
from app.video.asset_generators import AudioGenerationService, ImageGenerationService, ImageProvider
from app.video.visual_planner import VisualPlannerService
from app.video.clip_renderer import SceneClipService, FinalRenderService
from datetime import datetime
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Video Pipeline (Phase 2)"])


# ── Internal Helpers ────────────────────────────────────────────────────────

def _get_project_metadata(project_id: str) -> ProjectMetadata:
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project or scenes not found for this document.")
    return metadata

def _get_scene(project_id: str, scene_id: str) -> SceneResponse:
    metadata = _get_project_metadata(project_id)
    for scene in metadata.scenes:
        if scene.scene_id == scene_id:
            return scene
    raise HTTPException(status_code=404, detail=f"Scene {scene_id} not found in project {project_id}")

def _update_scene(project_id: str, scene_id: str, scene: SceneResponse):
    scene.last_updated = datetime.now().isoformat()
    ProjectMetadataManager.update_scene_status(project_id, scene_id, scene)


# ── Core Video Endpoints ────────────────────────────────────────────────────

@router.post("/scripts/{project_id}/segment-scenes", response_model=ProjectMetadata)
async def segment_scenes(project_id: str):
    """
    Reads the Phase 1 generated Script Response for a specific project
    and segments it into renderable modular scenes.
    """
    _get_doc(project_id)  # Validate project exists
    
    script_resp = _load_script(project_id)
    if not script_resp:
        raise HTTPException(status_code=404, detail="Script not generated for this document yet.")
        
    try:
        ProjectMetadataManager.setup_project_directories(project_id)
        
        # Deterministically convert script sections to scenes
        metadata = segmenter.segment_script(project_id, script_resp)
        ProjectMetadataManager.save_metadata(metadata)
        
        return metadata
    except Exception as e:
        logger.error(f"Scene segmentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenes/{scene_id}/generate-audio", response_model=SceneResponse)
async def generate_scene_audio(project_id: str, scene_id: str, request: AssetGenerationRequest = AssetGenerationRequest()):
    """Generate the Edge-TTS narration audio for a single scene."""
    scene = _get_scene(project_id, scene_id)
    
    scene.audio_status = AssetStatus.GENERATING
    _update_scene(project_id, scene_id, scene)
    
    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    audio_path = os.path.join(proj_dir, "audio", f"{scene_id}.mp3")
    
    try:
        duration = await AudioGenerationService.generate_audio(
            text=scene.narration_text,
            output_path=audio_path,
            voice=request.voice
        )
        
        scene.audio_path = audio_path
        scene.actual_duration = duration
        scene.audio_status = AssetStatus.READY
        scene.clip_status = AssetStatus.MISSING  # Mark clip as needing rebuild
        scene.status = SceneStatus.PROCESSING
    except Exception as e:
        scene.audio_status = AssetStatus.ERROR
        scene.error_message = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _update_scene(project_id, scene_id, scene)
        
    return scene


@router.post("/scenes/{scene_id}/analyze-visual", response_model=SceneResponse)
async def analyze_scene_visual(project_id: str, scene_id: str, request: AssetGenerationRequest = AssetGenerationRequest()):
    """Preview the enriched visual plan without generating the image (Phase 5)."""
    scene = _get_scene(project_id, scene_id)
    
    visual_plan = await VisualPlannerService.enrich_scene_visuals(scene, request.image_style)
    scene.concept_summary = visual_plan.concept_summary
    scene.visual_type = visual_plan.visual_type
    scene.enriched_prompt = visual_plan.enriched_image_prompt
    scene.negative_prompt = visual_plan.negative_prompt
    scene.style_preset = request.image_style
    scene.prompt_candidates = visual_plan.prompt_candidates
    scene.debug_logs = visual_plan.debug_logs
    
    ProjectMetadataManager.update_scene_status(project_id, scene_id, scene)
    return scene


@router.post("/scenes/{scene_id}/generate-image", response_model=SceneResponse)
async def generate_scene_image(project_id: str, scene_id: str, request: AssetGenerationRequest = AssetGenerationRequest()):
    """Generate the scene visual."""
    scene = _get_scene(project_id, scene_id)
    
    scene.image_status = AssetStatus.GENERATING
    _update_scene(project_id, scene_id, scene)
    
    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    image_path = os.path.join(proj_dir, "images", f"{scene_id}.jpg")
    
    try:
        # User explicitly wants a custom prompt
        if request.custom_prompt:
            scene.enriched_prompt = request.custom_prompt
            scene.style_preset = request.image_style
            
        # Enrich if missing
        elif not scene.enriched_prompt:
            visual_plan = await VisualPlannerService.enrich_scene_visuals(scene, request.image_style)
            scene.enriched_prompt = visual_plan.enriched_image_prompt
            scene.negative_prompt = visual_plan.negative_prompt
            scene.style_preset = request.image_style
            
        await ImageGenerationService.generate_image(
            prompt=scene.enriched_prompt or scene.visual_prompt,
            output_path=image_path,
            style_preset=scene.style_preset,
            negative_prompt=scene.negative_prompt,
            provider=request.image_provider or scene.image_provider or ImageProvider.STABILITY.value
        )
        
        scene.image_path = image_path
        scene.image_status = AssetStatus.READY
        scene.clip_status = AssetStatus.MISSING  # Mark clip as needing rebuild
        scene.status = SceneStatus.PROCESSING
    except Exception as e:
        scene.image_status = AssetStatus.ERROR
        scene.error_message = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _update_scene(project_id, scene_id, scene)
        
    return scene


@router.post("/scenes/{scene_id}/generate-clip", response_model=SceneResponse)
async def generate_scene_clip(project_id: str, scene_id: str):
    """Combines the generated image and audio into an MP4 clip."""
    scene = _get_scene(project_id, scene_id)
    
    if not scene.audio_path or not scene.image_path:
        raise HTTPException(status_code=400, detail="Ensure both audio and image are generated before rendering clip.")
        
    scene.clip_status = AssetStatus.GENERATING
    _update_scene(project_id, scene_id, scene)
    
    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    clip_path = os.path.join(proj_dir, "clips", f"{scene_id}.mp4")
    
    try:
        SceneClipService.render_scene_clip(
            image_path=scene.image_path,
            audio_path=scene.audio_path,
            output_path=clip_path
        )
        scene.clip_path = clip_path
        scene.clip_status = AssetStatus.READY
        scene.status = SceneStatus.COMPLETED
    except Exception as e:
        scene.clip_status = AssetStatus.ERROR
        scene.error_message = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _update_scene(project_id, scene_id, scene)
        
    return scene


# ── Full Pipeline & Status Endpoints ────────────────────────────────────────

@router.get("/projects/{project_id}/scenes", response_model=ProjectMetadata)
async def get_project_scenes(project_id: str):
    """Retrieve full project timeline and metadata."""
    return _get_project_metadata(project_id)


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(project_id: str, scene_id: str):
    """Retrieve specific scene state."""
    return _get_scene(project_id, scene_id)


async def _process_all_scenes_bg(project_id: str, req: AssetGenerationRequest):
    """Background task to fully render all un-rendered assets in a project sequentially."""
    try:
        metadata = ProjectMetadataManager.load_metadata(project_id)
        if not metadata:
            return
            
        proj_dir = ProjectMetadataManager.get_project_dir(project_id)
            
        for scene in metadata.scenes:
            # 1. Audio
            if not scene.audio_path or scene.audio_status != AssetStatus.READY:
                scene.audio_status = AssetStatus.GENERATING
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
                
                audio_path = os.path.join(proj_dir, "audio", f"{scene.scene_id}.mp3")
                dur = await AudioGenerationService.generate_audio(scene.narration_text, audio_path, req.voice)
                scene.audio_path = audio_path
                scene.actual_duration = dur
                scene.audio_status = AssetStatus.READY
                scene.clip_status = AssetStatus.MISSING
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
                
            # 2. Image
            if not scene.image_path or scene.image_status != AssetStatus.READY:
                scene.image_status = AssetStatus.GENERATING
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
                
                img_path = os.path.join(proj_dir, "images", f"{scene.scene_id}.jpg")
                if not scene.enriched_prompt:
                    visual_plan = await VisualPlannerService.enrich_scene_visuals(scene, req.image_style)
                    scene.enriched_prompt = visual_plan.enriched_image_prompt
                    scene.negative_prompt = visual_plan.negative_prompt
                    scene.style_preset = req.image_style
                
                await ImageGenerationService.generate_image(
                    prompt=scene.enriched_prompt or scene.visual_prompt, 
                    output_path=img_path, 
                    style_preset=scene.style_preset,
                    negative_prompt=scene.negative_prompt,
                    provider=req.image_provider or scene.image_provider or ImageProvider.STABILITY.value
                )
                scene.image_path = img_path
                scene.image_status = AssetStatus.READY
                scene.clip_status = AssetStatus.MISSING
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
                
            # 3. Clip
            if not scene.clip_path or scene.clip_status != AssetStatus.READY:
                scene.clip_status = AssetStatus.GENERATING
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
                
                clip_path = os.path.join(proj_dir, "clips", f"{scene.scene_id}.mp4")
                SceneClipService.render_scene_clip(scene.image_path, scene.audio_path, clip_path)
                scene.clip_path = clip_path
                scene.clip_status = AssetStatus.READY
                scene.status = SceneStatus.COMPLETED
                ProjectMetadataManager.update_scene_status(project_id, scene.scene_id, scene)
            
        # Finalization
        metadata = ProjectMetadataManager.load_metadata(project_id)
        metadata.timeline_path = TimelineService.generate_timeline(metadata)
        ProjectMetadataManager.save_metadata(metadata)
        logger.info(f"Background rendering entirely completed for project {project_id}")
        
    except Exception as e:
        logger.error(f"Background cascade rendering failed for {project_id}: {e}")


@router.post("/projects/{project_id}/generate-all-scenes")
async def generate_all_scenes(project_id: str, background_tasks: BackgroundTasks, request: AssetGenerationRequest = AssetGenerationRequest()):
    """Async trigger to run audio+image+clip for all scenes."""
    _get_project_metadata(project_id) # validates project
    logger.info(f"Kicking off background asset generation for project {project_id}...")
    
    background_tasks.add_task(_process_all_scenes_bg, project_id, request)
    return {"status": "started", "message": "Background generation of all scenes has commenced."}


@router.post("/projects/{project_id}/generate-scene-clips")
async def generate_scene_clips(project_id: str):
    """
    Phase 4: Render individual video clips for ALL scenes in a project.
    Each clip is a combination of the scene's image and audio.
    """
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project metadata not found.")

    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    clips_dir = os.path.join(proj_dir, "clips")

    rendered_count = 0
    errors = []

    for scene in metadata.scenes:
        if not scene.image_path or not scene.audio_path:
            logger.warning(f"Skipping scene {scene.scene_id}: missing image or audio.")
            continue

        clip_filename = f"{scene.scene_id}.mp4"
        clip_path = os.path.join(clips_dir, clip_filename)

        try:
            # We render each scene clip independently
            SceneClipService.render_scene_clip(
                image_path=scene.image_path,
                audio_path=scene.audio_path,
                output_path=clip_path
            )
            scene.clip_path = clip_path
            scene.status = SceneStatus.COMPLETED
            rendered_count += 1
        except Exception as e:
            logger.error(f"Failed to render clip for scene {scene.scene_id}: {e}")
            scene.status = SceneStatus.FAILED
            scene.error_message = str(e)
            errors.append(f"{scene.scene_id}: {str(e)}")

    ProjectMetadataManager.save_metadata(metadata)
    
    return {
        "project_id": project_id,
        "rendered_count": rendered_count,
        "failed_count": len(errors),
        "errors": errors
    }


@router.post("/projects/{project_id}/render-final-video")
async def render_final_video(project_id: str):
    """Concat all scene clips into the final video export."""
    metadata = _get_project_metadata(project_id)
    clip_paths = []
    for scene in sorted(metadata.scenes, key=lambda s: s.scene_order):
        if scene.clip_path and os.path.exists(scene.clip_path):
            clip_paths.append(scene.clip_path)

    if not clip_paths:
        raise HTTPException(status_code=400, detail="No pre-rendered scene clips found.")

    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    final_output_path = os.path.join(proj_dir, "renders", "final_video.mp4")

    try:
        FinalRenderService.concatenate_scene_clips(clip_paths, final_output_path)
        metadata.final_video_path = final_output_path
        ProjectMetadataManager.save_metadata(metadata)
        return {"status": "success", "final_video_path": final_output_path}
    except Exception as e:
        logger.error(f"Final render failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/scenes/{scene_id}/narration", response_model=SceneResponse)
async def update_scene_narration(project_id: str, scene_id: str, narration: str):
    """Update scene narration text, marking audio and clip as missing."""
    scene = _get_scene(project_id, scene_id)
    scene.narration_text = narration
    scene.audio_status = AssetStatus.MISSING
    scene.clip_status = AssetStatus.MISSING
    scene.status = SceneStatus.PROCESSING
    _update_scene(project_id, scene_id, scene)
    return scene

@router.patch("/scenes/{scene_id}/prompt", response_model=SceneResponse)
async def update_scene_prompt(project_id: str, scene_id: str, prompt: str):
    """Update enriched image prompt, marking image and clip as missing."""
    scene = _get_scene(project_id, scene_id)
    scene.enriched_prompt = prompt
    scene.image_status = AssetStatus.MISSING
    scene.clip_status = AssetStatus.MISSING
    scene.status = SceneStatus.PROCESSING
    _update_scene(project_id, scene_id, scene)
    return scene

@router.post("/projects/{project_id}/rebuild-video")
async def rebuild_final_video(project_id: str):
    """
    FAST rebuild by concatenating already rendered clips.
    If a clip is missing but source assets (IMG/AUD) are ready, it renders it on-the-fly.
    """
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project metadata not found.")

    proj_dir = ProjectMetadataManager.get_project_dir(project_id)
    clips_dir = os.path.join(proj_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    clip_paths = []
    scenes_to_render = []
    
    # 1. Identify what we have and what we need
    for scene in sorted(metadata.scenes, key=lambda s: s.scene_order):
        if scene.clip_path and os.path.exists(scene.clip_path):
            clip_paths.append(scene.clip_path)
        elif scene.image_path and os.path.exists(scene.image_path) and \
             scene.audio_path and os.path.exists(scene.audio_path):
            scenes_to_render.append(scene)
        else:
            # Truly missing assets
            logger.warning(f"Scene {scene.scene_id} is missing source assets for rebuild.")
            
    # 2. Render missing clips if any
    if scenes_to_render:
        logger.info(f"Rebuild: Rendering {len(scenes_to_render)} missing clips on-the-fly.")
        for scene in scenes_to_render:
            try:
                clip_filename = f"{scene.scene_id}.mp4"
                clip_path = os.path.join(clips_dir, clip_filename)
                SceneClipService.render_scene_clip(
                    image_path=scene.image_path,
                    audio_path=scene.audio_path,
                    output_path=clip_path
                )
                scene.clip_path = clip_path
                scene.clip_status = AssetStatus.READY
                scene.status = SceneStatus.COMPLETED
                clip_paths.append(clip_path)
            except Exception as e:
                logger.error(f"Rebuild: Failed to render clip for {scene.scene_id}: {e}")

        # Save metadata after rendering missing clips
        ProjectMetadataManager.save_metadata(metadata)

    # 3. Final Concatenation
    if not clip_paths:
        raise HTTPException(status_code=400, detail="No clips found or source assets missing to rebuild.")
        
    final_output_path = os.path.join(proj_dir, "renders", "final_video.mp4")
    os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
    
    try:
        FinalRenderService.concatenate_scene_clips(clip_paths, final_output_path)
        metadata.final_video_path = final_output_path
        ProjectMetadataManager.save_metadata(metadata)
        return {"status": "success", "final_video_path": final_output_path}
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scenes/{scene_id}/preview")
async def preview_scene_clip(project_id: str, scene_id: str):
    """Preview a single scene's MP4 clip."""
    scene = _get_scene(project_id, scene_id)
    if not scene.clip_path or not os.path.exists(scene.clip_path):
        raise HTTPException(status_code=404, detail="Scene clip not found.")
    return FileResponse(scene.clip_path, media_type="video/mp4")

@router.get("/projects/{project_id}/video")
async def get_project_video(project_id: str):
    """Serves the final movie file."""
    metadata = _get_project_metadata(project_id)
    if not metadata or not metadata.final_video_path:
        raise HTTPException(status_code=404, detail="Final video not yet rendered.")
    return FileResponse(metadata.final_video_path, media_type="video/mp4")
