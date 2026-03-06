import uuid
from typing import List

from app.models.schemas import ScriptResponse
from app.models.video_schemas import SceneResponse, ProjectMetadata


class SceneSegmentationService:
    """
    Transforms a generated ScriptResponse (Phase 1) into discrete, 
    renderable video Scene objects (Phase 2).
    
    Rather than calling an LLM again, this deterministically maps the highly 
    structured sections of the RAG script output into scenes.
    """

    @staticmethod
    def _estimate_duration(text: str, wpm: int = 150) -> float:
        """Estimate speech duration based on a standard words-per-minute rate."""
        if not text:
            return 0.0
        words = len(text.split())
        words_per_second = wpm / 60.0
        return round(words / words_per_second, 1)

    @classmethod
    def segment_script(cls, project_id: str, script: ScriptResponse) -> ProjectMetadata:
        """Convert a full video script into a series of independently renderable scenes."""
        scenes: List[SceneResponse] = []
        scene_counter = 1

        def add_scene(heading: str, narration: str, visual: str):
            nonlocal scene_counter
            if not narration.strip():
                return
                
            # Fallback visual if empty
            if not visual or not visual.strip():
                visual = f"cinematic, highly detailed, educational visualization for: {heading}"

            scene = SceneResponse(
                scene_id=f"{project_id}_scene_{scene_counter:03d}_{uuid.uuid4().hex[:6]}",
                project_id=project_id,
                scene_order=scene_counter,
                heading=heading,
                narration_text=narration,
                visual_prompt=visual,
                subtitle_text=narration,  # In a V3, this could be chunked for actual standard SRTs
                estimated_duration=cls._estimate_duration(narration)
            )
            scenes.append(scene)
            scene_counter += 1

        # 1. Hook
        if script.hook:
            add_scene(
                heading="Hook", 
                narration=script.hook, 
                visual=script.visual_cues[0] if script.visual_cues else "Captivating cinematic opening scene"
            )

        # 2. Introduction
        if script.introduction:
            add_scene(
                heading="Introduction",
                narration=script.introduction,
                visual="Educational animated introduction graphic"
            )

        # 3. Main Sections
        for section in script.main_sections:
            visual = section.suggested_visuals[0] if section.suggested_visuals else f"Infographic about {section.heading}"
            add_scene(
                heading=section.heading,
                narration=section.narration,
                visual=visual
            )

        # 4. Conclusion
        if script.conclusion:
            add_scene(
                heading="Conclusion",
                narration=script.conclusion,
                visual="Summary cinematic end card"
            )

        # 5. Takeaways (Optional - if we want a dedicated scene for it)
        if script.key_takeaways:
            takeaways_text = "Key takeaways: " + ". ".join(script.key_takeaways)
            add_scene(
                heading="Key Takeaways",
                narration=takeaways_text,
                visual="Bullet point list graphic summarizing key takeaways"
            )

        # Build project metadata tracker
        return ProjectMetadata(
            project_id=project_id,
            total_scenes=len(scenes),
            scenes=scenes
        )

# Create singleton instance
segmenter = SceneSegmentationService()
