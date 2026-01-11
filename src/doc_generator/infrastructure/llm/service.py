"""
LLM service for intelligent content transformation.

Provides OpenAI and Claude-powered content summarization, slide generation, and enhancement.
"""

import json
import os
import time
from typing import Optional

from loguru import logger

from ..settings import get_settings

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None
    logger.warning("google-genai not installed - Gemini LLM disabled")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not available")


class LLMService:
    """
    LLM service for intelligent content processing.

    Uses OpenAI GPT or Claude models for content summarization, slide generation,
    and executive presentation enhancement.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        provider: str = "openai",
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
            api_key: API key. If not provided, checks env vars (ANTHROPIC_API_KEY, CLAUDE_API_KEY, OPENAI_API_KEY)
            model: Model to use (default: gpt-4o-mini)
        """
        # Try to determine which API to use
        self.claude_api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        self.model = model
        self.client = None
        self.provider = None
        self.requested_provider = provider
        self.max_summary_points = max_summary_points
        self.max_slides = max_slides
        self.max_tokens_summary = max_tokens_summary
        self.max_tokens_slides = max_tokens_slides
        self.temperature_summary = temperature_summary
        self.temperature_slides = temperature_slides

        if provider == "gemini":
            if self.gemini_api_key and GENAI_AVAILABLE:
                self.client = genai.Client(api_key=self.gemini_api_key)
                self.provider = "gemini"
                logger.info(f"LLM service initialized with Gemini: {model}")
            else:
                logger.warning("Gemini requested but not available - LLM features disabled")
        elif provider == "openai" and self.openai_api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.openai_api_key)
            self.provider = "openai"
            logger.info(f"LLM service initialized with OpenAI: {model}")
        elif False and self.claude_api_key and ANTHROPIC_AVAILABLE:
            # Claude support disabled - use OpenAI instead
            self.client = Anthropic(api_key=self.claude_api_key)
            self.provider = "claude"
            if "gpt" in model.lower():
                self.model = "claude-sonnet-4-20250514"
            logger.info(f"LLM service initialized with Claude: {self.model}")
        else:
            logger.warning("Unsupported LLM provider requested - LLM features disabled")

    _total_calls: int = 0
    _models_used: set[str] = set()
    _providers_used: set[str] = set()
    _call_details: list[dict] = []

    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.client is not None

    def _call_llm(
        self,
        system_msg: str,
        user_msg: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool = False,
        step: str = "llm_call"
    ) -> str:
        """
        Call LLM provider (OpenAI or Claude).
        
        Args:
            system_msg: System message
            user_msg: User message
            max_tokens: Maximum tokens
            temperature: Temperature
            json_mode: Whether to use JSON mode
            
        Returns:
            Response text
        """
        if not self.is_available():
            return ""
            
        try:
            LLMService._total_calls += 1
            if self.model:
                LLMService._models_used.add(self.model)
            if self.provider:
                LLMService._providers_used.add(self.provider)
            logger.opt(colors=True).info(
                "<cyan>LLM call</cyan> provider={} model={}",
                self.provider,
                self.model
            )
            start_time = time.perf_counter()
            input_tokens = None
            output_tokens = None

            if self.provider == "gemini":
                prompt = user_msg
                if system_msg:
                    prompt = f"System: {system_msg}\n\nUser: {user_msg}"
                if json_mode:
                    prompt += "\n\nRespond with valid JSON only."
                if json_mode and types is not None:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json"
                        )
                    )
                else:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt
                    )
                usage = getattr(response, "usage_metadata", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_token_count", None)
                    output_tokens = getattr(usage, "candidates_token_count", None)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                LLMService._call_details.append({
                    "kind": "llm",
                    "step": step,
                    "provider": self.provider,
                    "model": self.model,
                    "duration_ms": duration_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                })
                response_text = (response.text or "").strip()
                return response_text
            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_msg,
                    messages=[{"role": "user", "content": user_msg}]
                )
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                LLMService._call_details.append({
                    "kind": "llm",
                    "step": step,
                    "provider": self.provider,
                    "model": self.model,
                    "duration_ms": duration_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                })
                return response.content[0].text
            else:  # openai
                kwargs = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                response = self.client.chat.completions.create(**kwargs)
                usage = getattr(response, "usage", None)
                if usage:
                    input_tokens = getattr(usage, "prompt_tokens", None)
                    output_tokens = getattr(usage, "completion_tokens", None)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                LLMService._call_details.append({
                    "kind": "llm",
                    "step": step,
                    "provider": self.provider,
                    "model": self.model,
                    "duration_ms": duration_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                })
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""

    def _safe_json_load(self, text: str) -> Optional[object]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start_idx = None
        for i, ch in enumerate(text):
            if ch in "{[":
                start_idx = i
                break
        if start_idx is None:
            return None

        stack = []
        for i in range(start_idx, len(text)):
            ch = text[i]
            if ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack:
                    continue
                stack.pop()
                if not stack:
                    candidate = text[start_idx:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
        return None

    @classmethod
    def usage_summary(cls) -> dict:
        return {
            "total_calls": cls._total_calls,
            "models": sorted(cls._models_used),
            "providers": sorted(cls._providers_used),
        }

    @classmethod
    def usage_details(cls) -> list[dict]:
        return list(cls._call_details)

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
        system_msg = "You are an executive communication specialist who creates clear, impactful summaries for senior leadership."
        user_msg = f"""Analyze the following content and create an executive summary suitable for senior leadership.

Requirements:
- Maximum {max_points} key points
- Focus on strategic insights, outcomes, and business impact
- Use clear, concise language
- Format as bullet points
- Each point should be 1-2 sentences max
- Use ONLY information present in the content; do not add new facts or assumptions

Content:
{content[:8000]}

Respond with ONLY the bullet points, no introduction or conclusion."""

        try:
            summary = self._call_llm(
                system_msg,
                user_msg,
                self.max_tokens_summary,
                self.temperature_summary,
                step="executive_summary"
            )
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
  - 3-4 bullet points (concise, 7-10 words max each)
  - Speaker notes (2-3 sentences for context)
- Focus on key messages that matter to senior leadership
- Use professional business language
- Structure for logical flow
 - Ensure bullet points are parallel in structure and style
- Use ONLY information from the content; do not introduce new facts or examples

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
            system_msg = "You are a presentation design expert who creates compelling executive presentations. Always respond with valid JSON."
            result = self._call_llm(
                system_msg,
                prompt,
                self.max_tokens_slides,
                self.temperature_slides,
                json_mode=True,
                step="slide_structure"
            )
            logger.debug(f"Slide structure raw response: {result[:200]}...")

            data = self._safe_json_load(result)
            if data is None:
                retry = self._call_llm(
                    system_msg,
                    prompt,
                    self.max_tokens_slides,
                    self.temperature_slides,
                    json_mode=True,
                    step="slide_structure:retry"
                )
                data = self._safe_json_load(retry)
            if data is None:
                raise ValueError("Invalid JSON response")

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

    def generate_slide_structure_from_sections(
        self,
        sections: list[dict],
        max_slides: Optional[int] = None
    ) -> list[dict]:
        """
        Generate slide structure aligned to explicit sections.

        Args:
            sections: List of section dicts with title, content, image_hint (optional)
            max_slides: Maximum number of slides (defaults to max_slides setting)

        Returns:
            List of slide dictionaries with title, bullets, speaker_notes, section_title
        """
        if not self.is_available() or not sections:
            return []

        max_slides = self.max_slides if max_slides is None else max_slides
        section_blocks = []
        for idx, section in enumerate(sections[:max_slides], 1):
            title = section.get("title", f"Section {idx}")
            content = section.get("content", "")
            image_hint = section.get("image_hint", "")
            snippet = content[:1200]
            section_blocks.append(
                f"Section {idx}: {title}\n"
                f"Image hint: {image_hint or 'None'}\n"
                f"Content:\n{snippet}\n"
            )

        prompt = f"""Create a presentation outline aligned to the sections below.

Requirements:
- One slide per section (maximum {max_slides})
- Title must match the section title exactly
- 3-4 bullet points per slide, 7-10 words max each
- Bullets should be parallel, action-led, and slide-ready
- Avoid filler phrases and long sentences
- Bullets should align to the section content and image hint
- Provide 1-2 sentence speaker notes per slide
- Use ONLY information from each section; do not add new facts or examples

Sections:
{chr(10).join(section_blocks)}

Respond in JSON format:
{{
  "slides": [
    {{
      "section_title": "Exact Section Title",
      "title": "Exact Section Title",
      "bullets": ["Point 1", "Point 2"],
      "speaker_notes": "Brief speaker notes"
    }}
  ]
}}"""

        try:
            system_msg = "You are a presentation designer creating concise, slide-ready content. Always respond with valid JSON."
            result = self._call_llm(
                system_msg,
                prompt,
                self.max_tokens_slides,
                self.temperature_slides,
                json_mode=True,
                step="section_slide_structure"
            )
            data = self._safe_json_load(result)
            if data is None:
                retry = self._call_llm(
                    system_msg,
                    prompt,
                    self.max_tokens_slides,
                    self.temperature_slides,
                    json_mode=True,
                    step="section_slide_structure:retry"
                )
                data = self._safe_json_load(retry)
            if data is None:
                raise ValueError("Invalid JSON response")

            slides = []
            if isinstance(data, dict):
                slides = data.get("slides", [])
            elif isinstance(data, list):
                slides = data

            valid_slides = []
            for slide in slides:
                if isinstance(slide, dict) and slide.get("title"):
                    valid_slides.append({
                        "section_title": slide.get("section_title", slide.get("title", "")),
                        "title": slide.get("title", ""),
                        "bullets": slide.get("bullets", slide.get("content", slide.get("points", []))),
                        "speaker_notes": slide.get("speaker_notes", slide.get("notes", ""))
                    })

            logger.debug(f"Generated section slide structure: {len(valid_slides)} slides")
            return valid_slides
        except Exception as e:
            logger.error(f"Failed to generate section slide structure: {e}")
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
            system_msg = "You are an executive communication specialist."
            result = self._call_llm(system_msg, prompt, 300, 0.3, step="enhance_bullets")
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
            system_msg = "You are a presentation coach."
            return self._call_llm(system_msg, prompt, 200, 0.4, step="speaker_notes")
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
            system_msg = "You are a data visualization expert."
            result = self._call_llm(
                system_msg,
                prompt,
                1000,
                0.3,
                json_mode=True,
                step="chart_suggestions"
            )
            data = self._safe_json_load(result)
            if data is None:
                retry = self._call_llm(
                    system_msg,
                    prompt,
                    1000,
                    0.3,
                    json_mode=True,
                    step="chart_suggestions:retry"
                )
                data = self._safe_json_load(retry)
            if data is None:
                raise ValueError("Invalid JSON response")
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
            system_msg = ("You are a visual communication expert who creates clear, informative diagrams. "
                         "You identify the best visualization type for each concept and structure data precisely. "
                         "Keep all text labels SHORT (under 20 chars) to prevent overlap in diagrams.")
            result = self._call_llm(
                system_msg,
                prompt,
                2000,
                0.4,
                json_mode=True,
                step="visualization_suggestions"
            )
            logger.debug(f"Visualization suggestions raw response: {result[:300]}...")
            data = self._safe_json_load(result)
            if data is None:
                retry = self._call_llm(
                    system_msg,
                    prompt,
                    2000,
                    0.4,
                    json_mode=True,
                    step="visualization_suggestions:retry"
                )
                data = self._safe_json_load(retry)
            if data is None:
                raise ValueError("Invalid JSON response")

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
        provider = llm_settings.content_provider or "openai"
        model = llm_settings.content_model or llm_settings.model
        _llm_service = LLMService(
            api_key=api_key,
            model=model,
            provider=provider,
            max_summary_points=llm_settings.max_summary_points,
            max_slides=llm_settings.max_slides,
            max_tokens_summary=llm_settings.max_tokens_summary,
            max_tokens_slides=llm_settings.max_tokens_slides,
            temperature_summary=llm_settings.temperature_summary,
            temperature_slides=llm_settings.temperature_slides,
        )
    return _llm_service
