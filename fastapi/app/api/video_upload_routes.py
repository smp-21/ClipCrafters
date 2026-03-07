"""
Video Upload and Processing Routes.
Handles video upload, frame extraction, script extraction, and video rebuilding.
"""

import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.core.logger import get_logger
from app.core.config import settings
from app.video.video_processor import VideoProcessorService
from app.video.mock_processor import MockVideoProcessorService
from app.video.script_extractor import ScriptExtractorService
from app.video.project_manager import ProjectMetadataManager
from app.models.video_schemas import ProjectMetadata, SceneResponse, AssetStatus, SceneStatus
from datetime import datetime
import uuid
import subprocess
import os

logger = get_logger(__name__)

router = APIRouter(prefix="/video-upload", tags=["Video Upload & Processing"])


# ── Helper Functions ────────────────────────────────────────────

def check_ffmpeg_available() -> tuple[bool, str]:
    """Check if FFmpeg is installed and available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "FFmpeg is available"
        return False, "FFmpeg command failed"
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg: https://ffmpeg.org/download.html"
    except Exception as e:
        return False, f"FFmpeg check failed: {str(e)}"


def check_ffprobe_available() -> tuple[bool, str]:
    """Check if FFprobe is installed and available."""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, "FFprobe is available"
        return False, "FFprobe command failed"
    except FileNotFoundError:
        return False, "FFprobe not found. Please install FFmpeg: https://ffmpeg.org/download.html"
    except Exception as e:
        return False, f"FFprobe check failed: {str(e)}"


def get_video_processor():
    """Get the appropriate video processor (real or mock)."""
    ffmpeg_ok, _ = check_ffmpeg_available()
    if ffmpeg_ok:
        return VideoProcessorService
    else:
        logger.warning("FFmpeg not available, using MockVideoProcessorService")
        return MockVideoProcessorService


# ── Test Endpoint ────────────────────────────────────────────────

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the route is working."""
    return {
        "status": "ok",
        "message": "Video upload routes are working",
        "endpoints": [
            "/video-upload/health",
            "/video-upload/test",
            "/video-upload/upload"
        ]
    }


# ── Health Check Endpoint ────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Check if FFmpeg is installed and available."""
    import subprocess
    
    try:
        # Check FFmpeg
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ffmpeg_available = result.returncode == 0
        ffmpeg_version = result.stdout.split('\n')[0] if ffmpeg_available else "Not found"
    except Exception as e:
        ffmpeg_available = False
        ffmpeg_version = f"Error: {str(e)}"
    
    try:
        # Check FFprobe
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ffprobe_available = result.returncode == 0
        ffprobe_version = result.stdout.split('\n')[0] if ffprobe_available else "Not found"
    except Exception as e:
        ffprobe_available = False
        ffprobe_version = f"Error: {str(e)}"
    
    # Check optional dependencies
    whisper_available = False
    try:
        import whisper
        whisper_available = True
    except ImportError:
        pass
    
    speech_recognition_available = False
    try:
        import speech_recognition
        speech_recognition_available = True
    except ImportError:
        pass
    
    return {
        "status": "healthy" if (ffmpeg_available and ffprobe_available) else "degraded",
        "ffmpeg": {
            "available": ffmpeg_available,
            "version": ffmpeg_version
        },
        "ffprobe": {
            "available": ffprobe_available,
            "version": ffprobe_version
        },
        "optional_dependencies": {
            "whisper": whisper_available,
            "speech_recognition": speech_recognition_available
        },
        "message": "FFmpeg is required for video processing" if not ffmpeg_available else "All systems operational"
    }


# ── Request/Response Models ────────────────────────────────────────

class VideoUploadResponse(BaseModel):
    project_id: str
    filename: str
    video_path: str
    metadata: dict
    message: str


class FrameExtractionResponse(BaseModel):
    project_id: str
    frame_count: int
    fps: float
    duration: float
    resolution: str
    frames_dir: str
    message: str


class ScriptExtractionResponse(BaseModel):
    project_id: str
    transcript: str
    language: str
    segments: List[dict]
    method: str
    message: str


class SceneDetectionResponse(BaseModel):
    project_id: str
    scene_count: int
    scenes: List[dict]
    message: str


class VideoRebuildResponse(BaseModel):
    project_id: str
    video_path: str
    frame_count: int
    duration: float
    message: str


class FrameUpdateRequest(BaseModel):
    frame_number: int
    image_data: Optional[str] = None  # Base64 encoded image


# ── Video Upload Endpoint ────────────────────────────────────────

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    extract_frames: bool = Query(False, description="Auto-extract frames"),
    extract_script: bool = Query(False, description="Auto-extract script"),
    detect_scenes: bool = Query(False, description="Auto-detect scenes")
):
    """
    Upload a video file and optionally extract frames, script, and detect scenes.
    
    Workflow:
    1. Upload video
    2. Extract metadata
    3. Optionally extract frames
    4. Optionally extract script/transcript
    5. Optionally detect scene changes
    
    Note: Set extract_* to False for faster upload without processing.
    """
    # Validate file type
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported: MP4, AVI, MOV, MKV, WEBM"
        )
    
    # Generate project ID
    project_id = str(uuid.uuid4())
    
    try:
        # Setup project directories
        project_dir = ProjectMetadataManager.get_project_dir(project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        videos_dir = os.path.join(project_dir, "videos")
        os.makedirs(videos_dir, exist_ok=True)
        
        # Save uploaded video
        video_filename = f"original_{file.filename}"
        video_path = os.path.join(videos_dir, video_filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Video uploaded: {video_path}")
        
        # Extract video metadata
        try:
            processor = get_video_processor()
            metadata = processor.get_video_metadata(video_path)
        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            # Provide default metadata if FFmpeg fails
            metadata = {
                "duration": 0,
                "fps": 30,
                "resolution": "unknown",
                "width": 0,
                "height": 0,
                "codec": "unknown",
                "bitrate": 0
            }
        
        # Create project metadata
        project_metadata = ProjectMetadata(
            project_id=project_id,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            video_path=video_path,
            video_metadata=metadata,
            scenes=[]
        )
        
        ProjectMetadataManager.save_metadata(project_metadata)
        
        # Auto-extract frames if requested
        if extract_frames:
            try:
                processor = get_video_processor()
                frames_dir = os.path.join(project_dir, "frames")
                frame_info = processor.extract_frames(video_path, frames_dir)
                project_metadata.frames_dir = frames_dir
                project_metadata.frame_count = frame_info["frame_count"]
                ProjectMetadataManager.save_metadata(project_metadata)
            except Exception as e:
                logger.error(f"Frame extraction failed: {e}")
        
        # Auto-extract script if requested
        if extract_script:
            try:
                transcript = await ScriptExtractorService.extract_script_from_video(video_path)
                project_metadata.transcript = transcript
                ProjectMetadataManager.save_metadata(project_metadata)
            except Exception as e:
                logger.error(f"Script extraction failed: {e}")
        
        # Auto-detect scenes if requested
        if detect_scenes:
            try:
                processor = get_video_processor()
                scenes = processor.detect_scenes(video_path)
                project_metadata.scene_timestamps = [s["timestamp"] for s in scenes]
                ProjectMetadataManager.save_metadata(project_metadata)
            except Exception as e:
                logger.error(f"Scene detection failed: {e}")
        
        return VideoUploadResponse(
            project_id=project_id,
            filename=file.filename,
            video_path=video_path,
            metadata=metadata,
            message="Video uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        # Cleanup on failure
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ── Frame Extraction Endpoint ────────────────────────────────────

@router.post("/projects/{project_id}/extract-frames", response_model=FrameExtractionResponse)
async def extract_frames_from_video(
    project_id: str,
    fps: Optional[int] = Query(None, description="FPS for extraction (None = all frames)")
):
    """Extract all frames from uploaded video."""
    # Check FFmpeg availability
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg_available()
    if not ffmpeg_ok:
        raise HTTPException(
            status_code=503,
            detail=f"FFmpeg is required but not available: {ffmpeg_msg}"
        )
    
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.video_path or not os.path.exists(metadata.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    try:
        processor = get_video_processor()
        project_dir = ProjectMetadataManager.get_project_dir(project_id)
        frames_dir = os.path.join(project_dir, "frames")
        
        # Extract frames
        frame_info = processor.extract_frames(
            metadata.video_path,
            frames_dir,
            fps=fps
        )
        
        # Update metadata
        metadata.frames_dir = frames_dir
        metadata.frame_count = frame_info["frame_count"]
        metadata.last_updated = datetime.now().isoformat()
        ProjectMetadataManager.save_metadata(metadata)
        
        return FrameExtractionResponse(
            project_id=project_id,
            frame_count=frame_info["frame_count"],
            fps=frame_info["fps"],
            duration=frame_info["duration"],
            resolution=frame_info["resolution"],
            frames_dir=frames_dir,
            message=f"Extracted {frame_info['frame_count']} frames successfully"
        )
        
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Frame extraction failed: {str(e)}. Make sure FFmpeg is installed and the video file is valid."
        )


# ── Script Extraction Endpoint ────────────────────────────────────

@router.post("/projects/{project_id}/extract-script", response_model=ScriptExtractionResponse)
async def extract_script_from_video(
    project_id: str,
    language: str = Query("en", description="Language code"),
    model: str = Query("base", description="Whisper model size")
):
    """Extract script/transcript from video audio."""
    # Check FFmpeg availability
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg_available()
    if not ffmpeg_ok:
        raise HTTPException(
            status_code=503,
            detail=f"FFmpeg is required but not available: {ffmpeg_msg}"
        )
    
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.video_path or not os.path.exists(metadata.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    try:
        # Extract transcript
        transcript = await ScriptExtractorService.extract_script_from_video(
            metadata.video_path,
            language=language,
            model=model
        )
        
        # Update metadata
        metadata.transcript = transcript
        metadata.last_updated = datetime.now().isoformat()
        ProjectMetadataManager.save_metadata(metadata)
        
        return ScriptExtractionResponse(
            project_id=project_id,
            transcript=transcript["text"],
            language=transcript["language"],
            segments=transcript["segments"],
            method=transcript["method"],
            message="Script extracted successfully" if transcript["text"] else "Script extraction completed but no text found (Whisper/SpeechRecognition may not be installed)"
        )
        
    except Exception as e:
        logger.error(f"Script extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Script extraction failed: {str(e)}. Install Whisper (pip install openai-whisper) for best results."
        )


# ── Scene Detection Endpoint ────────────────────────────────────

@router.post("/projects/{project_id}/detect-scenes", response_model=SceneDetectionResponse)
async def detect_video_scenes(
    project_id: str,
    threshold: float = Query(30.0, description="Scene detection threshold (0-100)")
):
    """Detect scene changes in video."""
    # Check FFmpeg availability
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg_available()
    if not ffmpeg_ok:
        raise HTTPException(
            status_code=503,
            detail=f"FFmpeg is required but not available: {ffmpeg_msg}"
        )
    
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.video_path or not os.path.exists(metadata.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    try:
        processor = get_video_processor()
        # Detect scenes
        scenes = processor.detect_scenes(metadata.video_path, threshold)
        
        # Create scene objects with script segments
        scene_objects = []
        if metadata.transcript and metadata.transcript.get("segments"):
            scene_timestamps = [s["timestamp"] for s in scenes]
            script_segments = ScriptExtractorService.segment_script_by_scenes(
                metadata.transcript,
                scene_timestamps
            )
            
            for i, (scene, script_seg) in enumerate(zip(scenes, script_segments)):
                scene_obj = SceneResponse(
                    scene_id=f"scene_{i:03d}",
                    project_id=project_id,
                    scene_order=i + 1,
                    heading=f"Scene {i+1}",
                    narration_text=script_seg["text"],
                    visual_prompt="",
                    subtitle_text=script_seg["text"],
                    estimated_duration=script_seg["duration"],
                    timestamp=scene["timestamp"],
                    status=SceneStatus.DRAFT
                )
                scene_objects.append(scene_obj)
                metadata.scenes.append(scene_obj)
        
        # Update metadata
        metadata.scene_timestamps = [s["timestamp"] for s in scenes]
        metadata.last_updated = datetime.now().isoformat()
        ProjectMetadataManager.save_metadata(metadata)
        
        return SceneDetectionResponse(
            project_id=project_id,
            scene_count=len(scenes),
            scenes=scenes,
            message=f"Detected {len(scenes)} scenes successfully"
        )
        
    except Exception as e:
        logger.error(f"Scene detection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scene detection failed: {str(e)}. Make sure FFmpeg is installed and the video file is valid."
        )
        ProjectMetadataManager.save_metadata(metadata)
        
        return SceneDetectionResponse(
            project_id=project_id,
            scene_count=len(scenes),
            scenes=scenes,
            message=f"Detected {len(scenes)} scenes successfully"
        )
        
    except Exception as e:
        logger.error(f"Scene detection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Scene detection failed: {str(e)}. Make sure FFmpeg is installed and the video file is valid."
        )


# ── Get Frames Endpoint ────────────────────────────────────────

@router.get("/projects/{project_id}/frames")
async def get_project_frames(
    project_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get list of extracted frames with pagination."""
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.frames_dir or not os.path.exists(metadata.frames_dir):
        raise HTTPException(status_code=404, detail="Frames not extracted yet")
    
    try:
        # Get all frame files
        frame_files = sorted([
            f for f in os.listdir(metadata.frames_dir)
            if f.endswith('.png')
        ])
        
        total_frames = len(frame_files)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        page_frames = frame_files[start_idx:end_idx]
        
        return {
            "project_id": project_id,
            "total_frames": total_frames,
            "page": page,
            "per_page": per_page,
            "total_pages": (total_frames + per_page - 1) // per_page,
            "frames": [
                {
                    "filename": f,
                    "frame_number": int(f.split('_')[1].split('.')[0]),
                    "url": f"/video-upload/projects/{project_id}/frames/{f}"
                }
                for f in page_frames
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get frames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Get Single Frame Endpoint ────────────────────────────────────

@router.get("/projects/{project_id}/frames/{filename}")
async def get_frame_image(project_id: str, filename: str):
    """Get a specific frame image."""
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.frames_dir:
        raise HTTPException(status_code=404, detail="Frames not extracted")
    
    frame_path = os.path.join(metadata.frames_dir, filename)
    
    if not os.path.exists(frame_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return FileResponse(frame_path, media_type="image/png")


# ── Update Frame Endpoint ────────────────────────────────────────

@router.put("/projects/{project_id}/frames/{frame_number}")
async def update_frame(
    project_id: str,
    frame_number: int,
    file: UploadFile = File(...)
):
    """Update/replace a specific frame."""
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.frames_dir:
        raise HTTPException(status_code=404, detail="Frames not extracted")
    
    try:
        # Save uploaded frame
        frame_filename = f"frame_{frame_number:05d}.png"
        frame_path = os.path.join(metadata.frames_dir, frame_filename)
        
        with open(frame_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Mark video as needing rebuild
        metadata.needs_rebuild = True
        metadata.last_updated = datetime.now().isoformat()
        ProjectMetadataManager.save_metadata(metadata)
        
        logger.info(f"Updated frame {frame_number} for project {project_id}")
        
        return {
            "project_id": project_id,
            "frame_number": frame_number,
            "message": "Frame updated successfully",
            "needs_rebuild": True
        }
        
    except Exception as e:
        logger.error(f"Frame update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Rebuild Video Endpoint ────────────────────────────────────────

@router.post("/projects/{project_id}/rebuild-from-frames", response_model=VideoRebuildResponse)
async def rebuild_video_from_frames(
    project_id: str,
    fps: int = Query(30, description="Output video FPS"),
    include_audio: bool = Query(True, description="Include original audio")
):
    """Rebuild video from frames (after editing)."""
    # Check FFmpeg availability
    ffmpeg_ok, ffmpeg_msg = check_ffmpeg_available()
    if not ffmpeg_ok:
        raise HTTPException(
            status_code=503,
            detail=f"FFmpeg is required but not available: {ffmpeg_msg}"
        )
    
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not metadata.frames_dir or not os.path.exists(metadata.frames_dir):
        raise HTTPException(status_code=404, detail="Frames not found. Please extract frames first.")
    
    try:
        project_dir = ProjectMetadataManager.get_project_dir(project_id)
        output_dir = os.path.join(project_dir, "videos")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"rebuilt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        processor = get_video_processor()
        
        # Extract audio if needed
        audio_path = None
        if include_audio and metadata.video_path and os.path.exists(metadata.video_path):
            try:
                audio_path = os.path.join(project_dir, "audio", "original_audio.mp3")
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                processor.extract_audio(metadata.video_path, audio_path)
            except Exception as e:
                logger.warning(f"Audio extraction failed, continuing without audio: {e}")
                audio_path = None
        
        # Rebuild video from frames
        video_path = processor.frames_to_video(
            frames_dir=metadata.frames_dir,
            output_path=output_path,
            fps=fps,
            audio_path=audio_path
        )
        
        # Get video metadata
        try:
            video_metadata = processor.get_video_metadata(video_path)
        except Exception as e:
            logger.warning(f"Failed to get video metadata: {e}")
            video_metadata = {"duration": 0}
        
        # Update project metadata
        metadata.rebuilt_video_path = video_path
        metadata.needs_rebuild = False
        metadata.last_updated = datetime.now().isoformat()
        ProjectMetadataManager.save_metadata(metadata)
        
        # Cleanup temp audio
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        
        return VideoRebuildResponse(
            project_id=project_id,
            video_path=video_path,
            frame_count=metadata.frame_count or 0,
            duration=video_metadata.get("duration", 0),
            message="Video rebuilt successfully from frames"
        )
        
    except Exception as e:
        logger.error(f"Video rebuild failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Video rebuild failed: {str(e)}. Make sure FFmpeg is installed and frames are valid."
        )


# ── Download Video Endpoint ────────────────────────────────────────

@router.get("/projects/{project_id}/download")
async def download_rebuilt_video(project_id: str):
    """Download the rebuilt video."""
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    video_path = metadata.rebuilt_video_path or metadata.video_path
    
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    filename = f"video_{project_id}.mp4"
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )


# ── Get Project Status Endpoint ────────────────────────────────────

@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get project processing status."""
    metadata = ProjectMetadataManager.load_metadata(project_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project_id,
        "has_video": bool(metadata.video_path),
        "has_frames": bool(metadata.frames_dir),
        "frame_count": metadata.frame_count or 0,
        "has_transcript": bool(metadata.transcript),
        "scene_count": len(metadata.scenes),
        "needs_rebuild": getattr(metadata, 'needs_rebuild', False),
        "has_rebuilt_video": bool(getattr(metadata, 'rebuilt_video_path', None)),
        "created_at": metadata.created_at,
        "last_updated": metadata.last_updated
    }
