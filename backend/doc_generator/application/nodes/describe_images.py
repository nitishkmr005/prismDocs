"""
Image description node for LangGraph workflow.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from ...domain.models import WorkflowState
from ...infrastructure.image import encode_image_base64
from ...infrastructure.observability.opik import log_llm_call
from ...infrastructure.settings import get_settings
from ...domain.prompts.image.image_generation_prompts import build_image_description_prompt
from ...utils.gemini_client import create_gemini_client, get_gemini_api_key

try:
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None


class GeminiImageDescriber:
    """Generate a blog-style description for an image using Gemini."""

    def __init__(self) -> None:
        """
        Invoked by: (no references found)
        """
        self.api_key = get_gemini_api_key()
        self.settings = get_settings()
        self.client = create_gemini_client(self.api_key)
        if self.api_key and self.client is None:
            logger.warning("google-genai not installed - image description disabled")

    def is_available(self) -> bool:
        """
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/describe_images.py, src/doc_generator/application/workflow/nodes/describe_images.py
        """
        return self.client is not None and types is not None

    def describe(self, section_title: str, content: str, image_path: Path) -> str:
        """
        Describe the image in a short blog-style paragraph.
        Invoked by: src/doc_generator/application/nodes/describe_images.py, src/doc_generator/application/workflow/nodes/describe_images.py
        """
        try:
            image_bytes = image_path.read_bytes()
        except Exception as exc:
            logger.warning(f"Failed to read image for description: {exc}")
            return ""

        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        prompt = build_image_description_prompt(section_title, content)
        model = self.settings.llm.content_model or self.settings.llm.model
        response = self.client.models.generate_content(
            model=model,
            contents=[prompt, image_part],
        )
        response_text = (response.text or "").strip()
        log_llm_call(
            name="image_description",
            prompt=prompt,
            response=response_text,
            provider="gemini",
            model=model,
            metadata={"section_title": section_title},
        )
        return response_text


def describe_images_node(state: WorkflowState) -> WorkflowState:
    """
    Generate descriptions and embed data for section images.
    Invoked by: src/doc_generator/application/graph_workflow.py, src/doc_generator/application/workflow/graph.py
    """
    from ...infrastructure.logging_utils import (
        log_node_start,
        log_node_end,
        log_progress,
        log_metric,
    )
    
    log_node_start("describe_images", step_number=6)
    
    structured_content = state.get("structured_content", {})
    section_images = structured_content.get("section_images", {})
    
    if not section_images:
        log_node_end("describe_images", success=True, details="No images to describe")
        return state

    log_metric("Images to Describe", len(section_images))
    
    markdown = structured_content.get("markdown", "")
    settings = get_settings()
    describer = GeminiImageDescriber()
    
    described_count = 0
    embedded_count = 0

    for idx, (section_id, info) in enumerate(section_images.items(), 1):
        section_title = info.get("section_title", "")
        log_progress(f"[{idx}/{len(section_images)}] {section_title}")
        
        image_path = Path(info.get("path", ""))
        if not image_path.exists():
            continue

        description = (info.get("description") or "").strip()
        if not description:
            if describer.is_available():
                description = describer.describe(
                    section_title=section_title,
                    content=markdown,
                    image_path=image_path,
                ).strip()
                if description:
                    described_count += 1
                else:
                    logger.error(f"Image description missing for section '{section_title}'")
            else:
                logger.error(f"Image description unavailable (Gemini not ready) for section '{section_title}'")
        info["description"] = description

        if settings.image_generation.embed_in_pdf and not info.get("embed_base64"):
            info["embed_base64"] = encode_image_base64(image_path)
            embedded_count += 1

    structured_content["section_images"] = section_images
    state["structured_content"] = structured_content
    
    log_metric("Descriptions Generated", described_count)
    log_metric("Images Embedded", embedded_count)
    log_node_end("describe_images", success=True, 
                details=f"{described_count} descriptions, {embedded_count} embedded")
    return state
