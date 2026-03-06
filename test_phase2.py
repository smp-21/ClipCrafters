import asyncio
import os
import json

from app.models.schemas import ScriptResponse
from app.video.scene_segmentation import segmenter
from app.video.asset_generators import AudioGenerationService, ImageGenerationService
from app.video.clip_renderer import SceneClipService
from app.video.project_manager import ProjectMetadataManager

async def test_generation():
    doc_id = "e608ddbdfe1947fd"
    script_path = f"app/storage/scripts/{doc_id}.json"
    
    if not os.path.exists(script_path):
        print(f"Test script {script_path} not found.")
        return
        
    with open(script_path, "r", encoding="utf-8") as f:
        data = f.read()
        
    print("1. Testing segment_script...")
    script_resp = ScriptResponse.model_validate_json(data)
    ProjectMetadataManager.setup_project_directories(doc_id)
    metadata = segmenter.segment_script(doc_id, script_resp)
    
    # Take the first scene to test
    scene = metadata.scenes[1] if len(metadata.scenes) > 1 else metadata.scenes[0]
    print(f"Selected Scene: {scene.heading}")
    print(f"Narration: {scene.narration_text[:50]}...")
    
    proj_dir = ProjectMetadataManager.get_project_dir(doc_id)
    audio_path = os.path.join(proj_dir, "audio", f"{scene.scene_id}.mp3")
    image_path = os.path.join(proj_dir, "images", f"{scene.scene_id}.jpg")
    clip_path = os.path.join(proj_dir, "clips", f"{scene.scene_id}.mp4")
    
    print("\n2. Testing AudioGenerationService...")
    dur = await AudioGenerationService.generate_audio(scene.narration_text, audio_path)
    print(f"Generated Audio. Duration: {dur} seconds at {audio_path}")
    
    print("\n3. Testing ImageGenerationService...")
    await ImageGenerationService.generate_image(scene.visual_prompt, image_path)
    print(f"Generated Image at {image_path}")
    
    print("\n4. Testing SceneClipService...")
    SceneClipService.render_scene_clip(image_path, audio_path, clip_path)
    print(f"Generated MP4 Clip at {clip_path}")
    print("\nAll pipeline components verified successfully!")

if __name__ == "__main__":
    asyncio.run(test_generation())
