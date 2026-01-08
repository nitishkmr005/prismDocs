"""
LLM service for intelligent content transformation.

Provides OpenAI-powered content summarization, slide generation, and enhancement.
"""

import json
import os
from typing import Optional

from loguru import logger
from openai import OpenAI

from .settings import get_settings


class LLMService:
    """
    LLM service for intelligent content processing.

    Uses OpenAI GPT models for content summarization, slide generation,
    and executive presentation enhancement.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_summary_points: int = 5,
        max_slides: int = 10,
        max_tokens_summary: int = 500,
        max_tokens_slides: int = 2000,
        temperature_summary: float = 0.3,
        temperature_slides: float = 0.4,
    ):
        """
        Initialize LLM service.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4o-mini for cost efficiency)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        self.max_summary_points = max_summary_points
        self.max_slides = max_slides
        self.max_tokens_summary = max_tokens_summary
        self.max_tokens_slides = max_tokens_slides
        self.temperature_summary = temperature_summary
        self.temperature_slides = temperature_slides

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"LLM service initialized with model: {model}")
        else:
            logger.warning("No OpenAI API key provided - LLM features disabled")

    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.client is not None

    def generate_executive_summary(self, content: str, max_points: Optional[int] = None) -> str:
        """
        Generate executive summary from content.

        Args:
            content: Raw content to summarize
            max_points: Maximum number of key points

        Returns:
            Executive summary as markdown bullet points
        """
        if not self.is_available():
            return ""

        max_points = self.max_summary_points if max_points is None else max_points
        prompt = f"""Analyze the following content and create an executive summary suitable for senior leadership.

Requirements:
- Maximum {max_points} key points
- Focus on strategic insights, outcomes, and business impact
- Use clear, concise language
- Format as bullet points
- Each point should be 1-2 sentences max

Content:
{content[:8000]}

Respond with ONLY the bullet points, no introduction or conclusion."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an executive communication specialist who creates clear, impactful summaries for senior leadership."},  # noqa: E501
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature_summary,
                max_tokens=self.max_tokens_summary
            )
            summary = response.choices[0].message.content.strip()
            logger.debug(f"Generated executive summary: {len(summary)} chars")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return ""

    def generate_slide_structure(self, content: str, max_slides: Optional[int] = None) -> list[dict]:
        """
        Generate optimized slide structure from content.

        Args:
            content: Markdown content to convert
            max_slides: Maximum number of content slides

        Returns:
            List of slide dictionaries with title, bullets, and speaker_notes
        """
        if not self.is_available():
            return []

        max_slides = self.max_slides if max_slides is None else max_slides
        prompt = f"""Convert the following content into a corporate presentation structure.

Requirements:
- Maximum {max_slides} slides (excluding title slide)
- Each slide should have:
  - A clear, action-oriented title (5-8 words)
  - 3-5 bullet points (concise, 10 words max each)
  - Speaker notes (2-3 sentences for context)
- Focus on key messages that matter to senior leadership
- Use professional business language
- Structure for logical flow

Content:
{content[:8000]}

Respond in JSON format:
{{
  "slides": [
    {{
      "title": "Slide Title",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "speaker_notes": "Context for the presenter..."
    }}
  ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a presentation design expert who creates compelling executive presentations. Always respond with valid JSON."},  # noqa: E501
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature_slides,
                max_tokens=self.max_tokens_slides,
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content.strip()
            logger.debug(f"Slide structure raw response: {result[:200]}...")

            data = json.loads(result)

            # Handle various response formats
            if isinstance(data, dict):
                slides = data.get("slides", data.get("presentation", data.get("content", [])))
                if not slides and len(data) == 1:
                    slides = list(data.values())[0]
            elif isinstance(data, list):
                slides = data
            else:
                slides = []

            # Validate slide structure
            valid_slides = []
            for slide in slides:
                if isinstance(slide, dict) and slide.get("title"):
                    valid_slides.append({
                        "title": slide.get("title", ""),
                        "bullets": slide.get("bullets", slide.get("content", slide.get("points", []))),
                        "speaker_notes": slide.get("speaker_notes", slide.get("notes", ""))
                    })

            logger.debug(f"Generated slide structure: {len(valid_slides)} slides")
            return valid_slides
        except Exception as e:
            logger.error(f"Failed to generate slide structure: {e}")
            return []

    def enhance_bullet_points(self, bullets: list[str]) -> list[str]:
        """
        Enhance bullet points for executive presentation.

        Args:
            bullets: List of raw bullet points

        Returns:
            Enhanced bullet points
        """
        if not self.is_available() or not bullets:
            return bullets

        prompt = f"""Enhance these bullet points for an executive presentation.

Requirements:
- Start each with an action verb or key metric
- Keep each under 12 words
- Make them impactful and clear
- Maintain the original meaning

Bullet points:
{chr(10).join(f'- {b}' for b in bullets)}

Respond with ONLY the enhanced bullet points, one per line, starting with "-"."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an executive communication specialist."},  # noqa: E501
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            result = response.choices[0].message.content.strip()
            enhanced = [line.lstrip("- ").strip() for line in result.split("\n") if line.strip().startswith("-")]
            return enhanced if enhanced else bullets
        except Exception as e:
            logger.error(f"Failed to enhance bullets: {e}")
            return bullets

    def generate_speaker_notes(self, slide_title: str, slide_content: list[str]) -> str:
        """
        Generate speaker notes for a slide.

        Args:
            slide_title: Title of the slide
            slide_content: Bullet points on the slide

        Returns:
            Speaker notes text
        """
        if not self.is_available():
            return ""

        prompt = f"""Generate speaker notes for this presentation slide.

Slide Title: {slide_title}
Content:
{chr(10).join(f'- {c}' for c in slide_content)}

Requirements:
- 2-3 sentences providing context
- Include key talking points
- Professional tone

Respond with ONLY the speaker notes text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a presentation coach."},  # noqa: E501
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate speaker notes: {e}")
            return ""

    def suggest_chart_data(self, content: str) -> list[dict]:
        """
        Suggest charts/visualizations based on content.

        Args:
            content: Content to analyze

        Returns:
            List of chart suggestions with type, title, and data
        """
        if not self.is_available():
            return []

        prompt = f"""Analyze this content and suggest data visualizations.

Content:
{content[:4000]}

For each visualization opportunity, provide:
- chart_type: "bar", "pie", "line", or "comparison"
- title: Chart title
- data: List of {{label, value}} pairs (use realistic numbers if not explicit)

Return JSON object with a "charts" array. If no visualizations make sense, return {{"charts": []}}.

Example format:
{{"charts": [{{"chart_type": "bar", "title": "Revenue by Quarter", "data": [{{"label": "Q1", "value": 100}}]}}]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data visualization expert."},  # noqa: E501
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content.strip()
            data = json.loads(result)
            if isinstance(data, dict):
                charts = data.get("charts", data.get("data", []))
                if not charts and len(data) == 1:
                    charts = list(data.values())[0]
                return charts if isinstance(charts, list) else []
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            logger.error(f"Failed to suggest chart data: {e}")
            return []

    def suggest_visualizations(self, content: str, max_visuals: int = 3) -> list[dict]:
        """
        Analyze content and suggest visual diagrams.

        Automatically detects patterns in content that can be visualized as:
        - Architecture diagrams (system components, layers)
        - Flowcharts (processes, decisions, steps)
        - Comparison visuals (feature comparisons, options)
        - Concept maps (hierarchical relationships)
        - Mind maps (topic overviews)

        Args:
            content: Content to analyze for visualization opportunities
            max_visuals: Maximum number of visualizations to suggest

        Returns:
            List of visualization suggestions with type, title, and structured data
        """
        if not self.is_available():
            return []

        prompt = f"""Analyze this content and suggest visual diagrams that would help explain key concepts.
Look for:
1. System architectures or component relationships → architecture diagram
2. Step-by-step processes or decision flows → flowchart
3. Comparisons between options/features → comparison_visual
4. Hierarchical concept relationships → concept_map
5. Topic overviews with subtopics → mind_map

Content:
{content[:6000]}

For each visualization opportunity (maximum {max_visuals}), provide structured data.
IMPORTANT: Keep text labels short (max 20 characters) to prevent overlap.

Return JSON with "visualizations" array. Each visualization must have:
- type: "architecture", "flowchart", "comparison_visual", "concept_map", or "mind_map"
- title: Short descriptive title
- data: Type-specific structured data (see formats below)

Data formats:

For architecture:
{{
  "components": [{{"id": "1", "name": "Component Name", "layer": "frontend|backend|database|external|infrastructure"}}],
  "connections": [{{"from": "1", "to": "2", "label": "connection type"}}]
}}

For flowchart:
{{
  "nodes": [{{"id": "1", "type": "start|end|process|decision", "text": "Node text"}}],
  "edges": [{{"from": "1", "to": "2", "label": "optional label"}}]
}}

For comparison_visual:
{{
  "items": ["Option A", "Option B"],
  "categories": [{{"name": "Category", "scores": [8, 6]}}]
}}

For concept_map:
{{
  "concepts": [{{"id": "1", "text": "Concept", "level": 0}}],
  "relationships": [{{"from": "1", "to": "2", "label": "relates to"}}]
}}

For mind_map:
{{
  "central": "Main Topic",
  "branches": [{{"text": "Branch 1", "children": ["Sub 1.1", "Sub 1.2"]}}]
}}

If no good visualization opportunities exist, return {{"visualizations": []}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a visual communication expert who creates clear, informative diagrams. "
                                   "You identify the best visualization type for each concept and structure data precisely. "  # noqa: E501
                                   "Keep all text labels SHORT (under 20 chars) to prevent overlap in diagrams."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content.strip()
            logger.debug(f"Visualization suggestions raw response: {result[:300]}...")

            data = json.loads(result)

            # Handle various response formats
            if isinstance(data, dict):
                visuals = data.get("visualizations", data.get("visuals", []))
                if not visuals and len(data) == 1:
                    visuals = list(data.values())[0]
            elif isinstance(data, list):
                visuals = data
            else:
                visuals = []

            # Validate and clean visualizations
            valid_visuals = []
            valid_types = {"architecture", "flowchart", "comparison_visual", "concept_map", "mind_map"}

            for visual in visuals[:max_visuals]:
                if not isinstance(visual, dict):
                    continue

                vis_type = visual.get("type", "")
                if vis_type not in valid_types:
                    continue

                vis_data = visual.get("data", {})
                if not vis_data:
                    continue

                valid_visuals.append({
                    "type": vis_type,
                    "title": visual.get("title", f"{vis_type.replace('_', ' ').title()} Diagram"),
                    "data": vis_data
                })

            logger.info(f"Suggested {len(valid_visuals)} visualizations")
            return valid_visuals

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse visualization suggestions JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to suggest visualizations: {e}")
            return []


# Singleton instance with lazy initialization
_llm_service: Optional[LLMService] = None


def get_llm_service(api_key: Optional[str] = None) -> LLMService:
    """
    Get or create LLM service instance.

    Args:
        api_key: Optional API key to initialize with

    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        settings = get_settings()
        llm_settings = settings.llm
        _llm_service = LLMService(
            api_key=api_key,
            model=llm_settings.model,
            max_summary_points=llm_settings.max_summary_points,
            max_slides=llm_settings.max_slides,
            max_tokens_summary=llm_settings.max_tokens_summary,
            max_tokens_slides=llm_settings.max_tokens_slides,
            temperature_summary=llm_settings.temperature_summary,
            temperature_slides=llm_settings.temperature_slides,
        )
    return _llm_service
