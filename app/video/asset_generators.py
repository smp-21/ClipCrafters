import os
import aiohttp
import httpx
import urllib.parse
import asyncio
from typing import Optional

# We use edge-tts for high-quality, free async text-to-speech
import edge_tts
from moviepy import AudioFileClip

from app.core.config import settings
from app.core.logger import get_logger
from enum import Enum
from google import genai
from google.genai import types

logger = get_logger(__name__)


class AudioGenerationService:
    """Generates TTS audio files using edge-tts and computes their exact duration."""

    @staticmethod
    async def generate_audio(text: str, output_path: str, voice: str = "en-US-AriaNeural") -> Optional[float]:
        """
        Generate MP3 audio from text.
        Returns the exact duration of the generated audio in seconds.
        """
        try:
            logger.info(f"Generating TTS audio with voice {voice}...")
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            if os.path.exists(output_path):
                with AudioFileClip(output_path) as audio_clip:
                    duration = audio_clip.duration
                return duration
            return None

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            raise RuntimeError(f"Audio generation failed: {e}")


class ImageProvider(str, Enum):
    GEMINI = "gemini"
    POLLINATIONS = "pollinations"
    STABILITY = "stabilityai"
    REPLICATE = "replicate"


class ImageGenerationService:
    """
    Generates images using AI providers, acting as an abstraction layer for styles,
    educational prompt enrichment, and negative prompts.
    """

    STYLE_PRESETS = {
        "ghibli_studio": (
            "Studio Ghibli inspired educational illustration, warm hand-painted aesthetic, "
            "soft cinematic lighting, expressive but scientifically meaningful, visually rich, "
            "storybook quality, clean composition"
        ),
        "ghibli_educational": (
            "Studio Ghibli inspired educational scientific illustration, warm painterly textures, "
            "soft natural colors, magical but clear and instructional, child-friendly yet accurate"
        ),
        "textbook_diagram": (
            "clean textbook-style scientific diagram, highly legible educational composition, "
            "structured layout, clear focus on concept explanation, minimal background clutter"
        ),
        "scientific_infographic": (
            "scientific infographic style, explanatory layout, educational visual hierarchy, "
            "clean labels, concept-first composition, highly informative"
        ),
        "cinematic_educational": (
            "cinematic educational illustration, high detail, visually engaging, dramatic but accurate, "
            "clear teaching composition, concept-focused"
        ),
        "minimalist_biology": (
            "minimalist biology educational illustration, simple clean layout, uncluttered, "
            "focused on plant biology structures and processes"
        ),
        "storybook_science": (
            "friendly storybook science illustration, visually engaging for students, warm colors, "
            "educational but imaginative"
        ),
    }

    DEFAULT_NEGATIVE_PROMPT = (
        "blurry, low detail, low resolution, distorted anatomy, bad composition, generic wallpaper, "
        "random decorative art, irrelevant objects, unreadable labels, messy layout, extra objects, "
        "oversaturated, low educational value, poor scientific accuracy, abstract without explanation, "
        "text artifacts, watermark, logo, deformed plant structures, cropped subject"
    )

    @staticmethod
    def _normalize_style(style_preset: str) -> str:
        if not style_preset:
            return "cinematic_educational"
        return style_preset.strip().lower().replace(" ", "_")

    @staticmethod
    def _get_style_description(style_preset: str) -> str:
        normalized = ImageGenerationService._normalize_style(style_preset)
        return ImageGenerationService.STYLE_PRESETS.get(
            normalized,
            ImageGenerationService.STYLE_PRESETS["cinematic_educational"]
        )

    @staticmethod
    def _detect_domain_details(prompt: str) -> str:
        """
        Adds domain-aware educational instructions based on keywords present in the prompt.
        """
        p = prompt.lower()

        details = []

        if any(word in p for word in ["photosynthesis", "chloroplast", "chlorophyll", "plant cell", "leaf"]):
            details.append(
                "Focus on plant biology. Show the concept in an educational way using visible biological structures. "
                "If relevant, include chloroplasts, leaf tissue, plant cells, sunlight rays, and arrows showing energy or material flow."
            )

        if "chloroplast" in p or "chlorophyll" in p:
            details.append(
                "Show the inside of a plant cell or a clear close-up of chloroplast structures. "
                "If the concept involves absorption of sunlight, depict sunlight rays entering and being absorbed. "
                "Use process arrows and explanatory visual relationships."
            )

        if "sunlight" in p or "light energy" in p or "solar energy" in p:
            details.append(
                "Show sunlight rays clearly interacting with the biological subject. "
                "Depict the direction of light and how the light energy reaches the leaf or chloroplast. "
                "Use visual flow cues instead of symbolic icons only."
            )

        if any(word in p for word in ["process", "flow", "convert", "absorb", "reaction", "transform", "produce"]):
            details.append(
                "The image must explain a process, not just show objects. "
                "Use arrows, cause-and-effect composition, inputs and outputs, and a layout that teaches the transformation."
            )

        if any(word in p for word in ["glucose", "oxygen", "carbon dioxide", "water"]):
            details.append(
                "If relevant, visually include inputs and outputs of the process: carbon dioxide and water entering, glucose and oxygen leaving."
            )

        # AI and Machine Learning Domain
        if any(word in p for word in ["artificial intelligence", "ai", "machine learning", "neural network", "transformer", "llm"]):
            details.append(
                "Show stylized glowing neural networks, digital brain connections, or data flow visualizations. "
                "The aesthetic should be futuristic and tech-focused, showing the 'inside' of an AI system or interconnected data nodes. "
                "Keep it educational and clean, not just abstract noise."
            )

        if "education" in p or "learning" in p or "student" in p or "teacher" in p:
            details.append(
                "Integrate educational elements: a student interacting with digital interfaces, a futuristic classroom, "
                "or a visualization of knowledge being shared or synthesized. "
                "Focus on the intersection of human learning and technology."
            )

        if any(word in p for word in ["split-screen", "comparison", "compare", "versus", "vs"]):
            details.append(
                "Use a clear vertical split-screen composition to compare two states or concepts side-by-side. "
                "Ensure both sides are visually distinct and labeled if possible."
            )

        if not details:
            details.append(
                "Create an educational explanatory image with strong concept clarity, showing structure, mechanism, and meaningful relationships instead of generic decorative visuals."
            )

        return " ".join(details)

    @staticmethod
    def _build_high_quality_prompt(
        prompt: str,
        style_preset: str = "cinematic_educational",
        negative_prompt: Optional[str] = None,
        provider: str = "generic"
    ) -> tuple[str, str]:
        """
        Build a richer educational image prompt and a robust negative prompt.
        """
        style_description = ImageGenerationService._get_style_description(style_preset)
        domain_details = ImageGenerationService._detect_domain_details(prompt)

        positive_prompt = (
            "Create a high-quality educational visual that clearly explains the concept from the scene narration. "
            "This must be a concept-explaining image, not generic decorative art. "
            f"Primary concept: {prompt}. "
            f"{domain_details} "
            "Use a well-structured composition with the main subject centered and clearly visible. "
            "If the concept describes a process, visually show the process step or mechanism. "
            "If the concept describes internal biology, use cutaway, close-up, or cross-sectional framing where useful. "
            "Prefer scientifically meaningful details over abstract aesthetics. "
            "Make the image visually intuitive for students and useful in an educational explainer video. "
            "Add process arrows or flow indicators when needed. "
            "If labels are visually possible, keep them minimal and clear. "
            f"Style direction: {style_description}. "
            "Image quality requirements: highly detailed, sharp focus, professional educational illustration, "
            "clean background, strong subject separation, excellent composition, visually explanatory, polished render."
        )

        final_negative_prompt = (
            f"{ImageGenerationService.DEFAULT_NEGATIVE_PROMPT}, {negative_prompt}"
            if negative_prompt
            else ImageGenerationService.DEFAULT_NEGATIVE_PROMPT
        )

        logger.info(f"Built enhanced prompt for {provider}: {positive_prompt[:200]}...")
        logger.info(f"Built negative prompt for {provider}: {final_negative_prompt[:160]}...")

        return positive_prompt, final_negative_prompt

    @staticmethod
    async def generate_image(
        prompt: str,
        output_path: str,
        style_preset: str = "cinematic_educational",
        negative_prompt: Optional[str] = None,
        provider: str = ImageProvider.GEMINI.value
    ) -> str:
        """
        Produce an image from a prompt.
        Saves to output_path and returns the path on success.
        """
        logger.info(f"Generating image using provider {provider}...")

        if provider == ImageProvider.STABILITY.value or provider is None:
            return await ImageGenerationService.generate_image_with_stability(
                prompt, output_path, style_preset, negative_prompt
            )
        elif provider == ImageProvider.GEMINI.value:
            return await ImageGenerationService.generate_image_with_gemini(
                prompt, output_path, style_preset, negative_prompt
            )
        elif provider == ImageProvider.POLLINATIONS.value:
            return await ImageGenerationService._generate_pollinations(
                prompt, output_path, style_preset, negative_prompt
            )
        else:
            raise NotImplementedError(f"Image provider {provider} is not configured yet.")

    @staticmethod
    async def generate_image_with_stability(
        prompt: str,
        output_path: str,
        style_preset: str,
        negative_prompt: Optional[str]
    ) -> str:
        """
        Stability.ai Image Generation (Stable Diffusion 3).
        """
        api_key = settings.stability_api_key
        if not api_key or api_key == "your_stability_api_key_here":
            logger.warning("STABILITY_API_KEY missing or placeholder! Falling back to Gemini.")
            return await ImageGenerationService.generate_image_with_gemini(
                prompt, output_path, style_preset, negative_prompt
            )

        final_prompt, final_negative_prompt = ImageGenerationService._build_high_quality_prompt(
            prompt=prompt,
            style_preset=style_preset,
            negative_prompt=negative_prompt,
            provider="stabilityai"
        )

        logger.info(f"Stability.ai Prompt: '{final_prompt[:150]}...'")

        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

        headers = {
            "authorization": f"Bearer {api_key}",
            "accept": "image/*"
        }

        data = {
            "prompt": final_prompt,
            "negative_prompt": final_negative_prompt,
            "output_format": "jpeg",
            "model": "sd3-large-turbo"
        }

        try:
            async with httpx.AsyncClient() as client:
                files = {
                    "prompt": (None, final_prompt),
                    "negative_prompt": (None, final_negative_prompt),
                    "output_format": (None, "jpeg"),
                    "model": (None, "sd3-large-turbo")
                }
                
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Stability.ai image saved to {output_path}")
                    return output_path
                else:
                    logger.error(f"Stability.ai API Error ({response.status_code}): {response.text}")
                    raise RuntimeError(f"Stability.ai API returned {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Stability.ai generation failed: {e}")
            logger.info("Falling back to Gemini due to Stability.ai failure.")
            return await ImageGenerationService.generate_image_with_gemini(
                prompt, output_path, style_preset, negative_prompt
            )

    @staticmethod
    async def generate_image_with_gemini(
        prompt: str,
        output_path: str,
        style_preset: str,
        negative_prompt: Optional[str]
    ) -> str:
        """
        Gemini Imagen image generation.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY missing! Falling back to pollinations for safe execution.")
            return await ImageGenerationService._generate_pollinations(
                prompt, output_path, style_preset, negative_prompt
            )

        final_prompt, final_negative_prompt = ImageGenerationService._build_high_quality_prompt(
            prompt=prompt,
            style_preset=style_preset,
            negative_prompt=negative_prompt,
            provider="gemini"
        )

        logger.info(f"Gemini Imagen Prompt: '{final_prompt[:150]}...'")

        try:
            client = genai.Client(api_key=api_key)
            # Try multiple model variations
            models_to_try = [
                "imagen-3.0-generate-001", 
                "imagen-3.0-fast-generate-001",
                "imagen-2.0-generate-002"
            ]
            
            last_error = None
            for model_name in models_to_try:
                try:
                    logger.info(f"Attempting Gemini Imagen with model: {model_name}")
                    result = client.models.generate_images(
                        model=model_name,
                        prompt=final_prompt,
                        config=types.GenerateImagesConfig(
                            number_of_images=1,
                            output_mime_type="image/jpeg",
                            aspect_ratio="1:1"
                        )
                    )

                    for generated_image in result.generated_images:
                        with open(output_path, "wb") as f:
                            f.write(generated_image.image.image_bytes)
                        logger.info(f"Gemini image ({model_name}) saved to {output_path}")
                        return output_path
                except Exception as model_err:
                    logger.warning(f"Gemini model {model_name} failed: {model_err}")
                    last_error = model_err
                    continue

            raise last_error or RuntimeError("Gemini returned success but no images were generated.")

        except Exception as e:
            logger.error(f"Gemini Imagen generation failed: {e}")
            logger.info("Falling back to Pollinations due to Gemini failure.")
            return await ImageGenerationService._generate_pollinations(
                prompt, output_path, style_preset, negative_prompt
            )

    @staticmethod
    async def _generate_pollinations(
        prompt: str,
        output_path: str,
        style_preset: str,
        negative_prompt: Optional[str]
    ) -> str:
        """
        Pollinations fallback image generation with retries and deep-fallback.
        """
        final_prompt, final_negative_prompt = ImageGenerationService._build_high_quality_prompt(
            prompt=prompt,
            style_preset=style_preset,
            negative_prompt=negative_prompt,
            provider="pollinations"
        )

        import random
        import time
        
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    seed = random.randint(1, 1000000)
                    # Trim prompt for URL safety
                    display_prompt = final_prompt[:500]
                    encoded_prompt = urllib.parse.quote(display_prompt)
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
                    
                    if final_negative_prompt:
                        url += f"&negative={urllib.parse.quote(final_negative_prompt)}"

                    logger.info(f"Pollinations Attempt {attempt+1}: {final_prompt[:80]}...")
                    
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                if len(image_data) > 5000: # Ensure it's not a tiny error image
                                    with open(output_path, "wb") as f:
                                        f.write(image_data)
                                    logger.info(f"Pollinations SUCCESS (Attempt {attempt+1})")
                                    return output_path
                            
                            logger.warning(f"Pollinations attempt {attempt+1} got status {response.status}")
                except Exception as e:
                    logger.warning(f"Pollinations attempt {attempt+1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1) # Backoff
            
            raise RuntimeError("All Pollinations attempts failed.")

        except Exception as e:
            logger.warning(f"Primary pollinations image generation failed ({e}). Falling back to a dynamic educational image.")
            # Use a keyword-based fallback to avoid the "same library photo" issue
            keywords = ["education", "science", "technology", "learning", "innovation", "biology", "nature"]
            # Extract a likely good keyword from the prompt if possible
            prompt_words = [w.lower() for w in prompt.split() if len(w) > 4]
            search_term = prompt_words[0] if prompt_words else random.choice(keywords)
            
            # Use loremflickr with search term and random seed to ensure uniqueness
            seed = random.randint(1, 1000)
            fallback_url = f"https://loremflickr.com/1280/720/{search_term}?lock={seed}"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(fallback_url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            with open(output_path, "wb") as f:
                                f.write(image_data)
                            logger.info(f"Dynamic fallback image ({search_term}) saved to {output_path}")
                            return output_path
                        else:
                            raise RuntimeError(f"Dynamic fallback failed with status {response.status}")
            except Exception as e2:
                logger.error(f"Ultra-fallback failed: {e2}")
                # Create a simple colored placeholder as absolute last resort
                raise RuntimeError(f"All image generation methods failed for prompt '{prompt}'. Error: {e}")
