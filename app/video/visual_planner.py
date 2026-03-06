import os
import json
from enum import Enum
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.core.logger import get_logger
from app.models.video_schemas import SceneResponse, VisualConceptResponse

logger = get_logger(__name__)


class StylePreset(str, Enum):
    GHIBLI = "ghibli_educational"
    SCIENTIFIC = "scientific_infographic"
    TEXTBOOK = "textbook_diagram"
    CINEMATIC = "cinematic_educational"
    MINIMALIST = "minimalist_biology"
    STORYBOOK = "storybook_science"


VISUAL_PLANNER_PROMPT = """You are an expert educational visual designer and scientific storyboard prompt writer for an AI video generation system.

Your task is to convert scene narration into a high-quality image generation prompt that creates a visually explanatory educational image.

GOAL
The generated image must help the viewer understand the concept being narrated. Do not generate generic decorative art prompts. Generate prompts that explain the idea visually.

INPUT
Scene Heading: {heading}
Scene Narration: {narration}
Preferred Style Preset: {style_preset}

YOUR JOB
Analyze the narration and produce:
1. concept_summary
2. visual_type
3. enriched_image_prompt
4. negative_prompt
5. optional_labels
6. optional_composition_notes

RULES
1. Focus on educational clarity first.
2. If the narration describes a process, show the process visually.
3. If the narration describes a structure, show the structure clearly.
4. Include relationships, arrows, flows, inputs, outputs, and labeled parts when useful.
5. Avoid vague prompts like "beautiful biology art" or "animation of chloroplast".
6. Use style only as enhancement. Never let style remove scientific clarity.
7. Keep prompts detailed, concrete, and scene-specific.
8. Prefer visuals that a student can understand quickly.
9. Avoid generic backgrounds unless they help explain the concept.
10. If the narration is abstract, convert it into a visually teachable composition.

STYLE PRESET GUIDELINES
- ghibli_educational: warm, storybook-like, hand-painted feel, expressive but still clear and educational
- scientific_infographic: clean, labeled, diagrammatic, high clarity
- textbook_diagram: academic, simple background, strong labels, educational
- cinematic_educational: dramatic but concept-focused, visually rich
- minimalist_biology: clean, uncluttered, biology-focused explanatory image
- storybook_science: friendly and engaging for beginners

NEGATIVE PROMPT RULES
Include terms that reduce bad outputs such as:
- blurry, low detail, distorted anatomy, extra limbs, irrelevant objects, clutter, unreadable text, generic wallpaper, low educational value, messy composition

OUTPUT FORMAT
Return strict JSON in this format:
{{
  "concept_summary": "...",
  "visual_type": "...",
  "enriched_image_prompt": "...",
  "negative_prompt": "...",
  "prompt_candidates": {{
     "scientific_diagram": "...",
     "educational_illustration": "...",
     "cinematic_educational": "..."
  }},
  "optional_labels": ["...", "..."],
  "optional_composition_notes": "..."
}}
"""

REWRITE_PROMPT_TEMPLATE = """You are an expert educational visual designer and scientific storyboard prompt writer for an AI video generation system.
Your task is to convert narration into a visual prompt that clearly explains the concept.

RULES:
- show the mechanism or process visually
- include important entities
- include arrows showing relationships if needed
- show inputs and outputs if relevant
- use composition that teaches the concept
- avoid generic words (educational graphic, nice illustration, background)
- prefer scientific diagrams or educational illustrations
- ensure visual clarity, style must support learning

Original Vague Prompt: {prompt}
Scene Narration: {narration}

Return ONLY the rewritten prompt string, nothing else.
"""

class VisualPlannerService:
    @staticmethod
    def get_llm():
        return ChatGroq(
            api_key=settings.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2
        )

    @staticmethod
    def get_json_llm():
        return ChatGroq(
            api_key=settings.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.2,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    @staticmethod
    def validate_visual_prompt(prompt: str) -> bool:
        """Returns True if the prompt is valid and highly detailed, False if it's too vague/generic."""
        if not prompt or len(prompt.split()) < 8:
            return False
            
        banned_phrases = [
            "educational graphic", "animation of", "nice illustration", 
            "background", "concept art", "simple diagram"
        ]
        prompt_lower = prompt.lower()
        if any(phrase in prompt_lower for phrase in banned_phrases):
            return False
            
        return True

    @classmethod
    async def rewrite_visual_prompt(cls, vague_prompt: str, narration: str) -> str:
        """Rewrites a vague prompt using the expert Groq LLM to make it educational and specific."""
        logger.info(f"Prompt failed validation, rewriting: '{vague_prompt}'")
        rewrite_template = PromptTemplate.from_template(REWRITE_PROMPT_TEMPLATE)
        chain = rewrite_template | cls.get_llm()
        res = chain.invoke({"prompt": vague_prompt, "narration": narration})
        rewritten = res.content.strip()
        logger.info(f"Rewritten prompt: '{rewritten}'")
        return rewritten

    @classmethod
    async def enrich_scene_visuals(cls, scene: SceneResponse, style_preset: str = StylePreset.CINEMATIC.value) -> VisualConceptResponse:
        """Analyzes a scene's narration and returns a rich visual prompt plan."""
        logger.info(f"Enriching visual prompt for Scene: {scene.scene_id} using style: {style_preset}")
        
        prompt = PromptTemplate.from_template(VISUAL_PLANNER_PROMPT)
        llm = cls.get_json_llm()
        
        chain = prompt | llm
        
        try:
            res = chain.invoke({
                "heading": scene.heading,
                "narration": scene.narration_text,
                "style_preset": style_preset
            })
            
            # Parse output - handle code blocks if LLM returns them
            content = res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            enriched_prompt = data.get("enriched_image_prompt", scene.visual_prompt)
            prompt_candidates = data.get("prompt_candidates", {})
            debug_logs = [f"Initial analysis generated: '{enriched_prompt[:50]}...'"]
            
            # Phase 5: Prompt Validation Stage
            if not cls.validate_visual_prompt(enriched_prompt):
                debug_logs.append(f"Validation FAILED for: '{enriched_prompt[:30]}...' (Too vague or restricted phrases found)")
                enriched_prompt = await cls.rewrite_visual_prompt(enriched_prompt, scene.narration_text)
                debug_logs.append(f"PROMPT REWRITTEN to: '{enriched_prompt[:50]}...'")
            else:
                debug_logs.append("Validation PASSED. Prompt is sufficiently descriptive.")

            return VisualConceptResponse(
                concept_summary=data.get("concept_summary", ""),
                visual_type=data.get("visual_type", ""),
                enriched_image_prompt=enriched_prompt,
                negative_prompt=data.get("negative_prompt", "blurry, generic"),
                prompt_candidates=prompt_candidates,
                debug_logs=debug_logs,
                optional_labels=data.get("optional_labels", []),
                optional_composition_notes=data.get("optional_composition_notes", "")
            )
            
        except Exception as e:
            logger.error(f"Failed to generate enriched visual plan: {e}")
            # Improved Fallback: Use narration as context for the prompt
            fallback_prompt = f"Educational visualization of: {scene.narration_text[:100]}..."
            if scene.visual_prompt and len(scene.visual_prompt) > 10:
                fallback_prompt = scene.visual_prompt

            return VisualConceptResponse(
                concept_summary="Fallback Generation",
                visual_type="Generic Educational",
                enriched_image_prompt=fallback_prompt,
                negative_prompt="blurry, distorted, unrelated, text-heavy",
                optional_labels=[],
                optional_composition_notes="Automatically generated fallback prompt"
            )
