"""
Claude-powered SVG generator for professional diagrams.

Uses Claude Sonnet 4.5 to generate high-quality SVG visualizations for
architecture diagrams, flowcharts, mind maps, and comparison visuals.
"""

import json
import os
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from loguru import logger

from .settings import get_settings


class ClaudeSVGGenerator:
    """
    Generate professional SVG diagrams using Claude Sonnet 4.5.

    Uses Claude's advanced reasoning to create well-structured, visually
    appealing SVG code for complex diagrams.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude SVG generator.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.settings = get_settings()
        self.llm_settings = self.settings.llm

        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Claude SVG generator initialized with model: {self.llm_settings.claude_model}")
        else:
            logger.warning("No Anthropic API key provided - Claude SVG generation disabled")

    def is_available(self) -> bool:
        """Check if Claude SVG generator is available."""
        return self.client is not None and self.llm_settings.use_claude_for_visuals

    def generate_architecture_diagram(
        self,
        title: str,
        data: dict,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate architecture diagram SVG using Claude.

        Args:
            title: Diagram title
            data: Architecture data with components and connections
            output_path: Optional path to save SVG

        Returns:
            SVG code as string
        """
        if not self.is_available():
            return ""

        components = data.get("components", [])
        connections = data.get("connections", [])

        prompt = f"""Generate a professional SVG architecture diagram with the following specifications:

Title: {title}

Components:
{json.dumps(components, indent=2)}

Connections:
{json.dumps(connections, indent=2)}

Requirements:
1. Create a clean, professional architecture diagram in SVG format
2. Use a modern color palette (teal #1E5D5A for backend, blue #2E86AB for frontend, magenta #A23B72 for database, orange #D76B38 for external services)
3. Components should be rounded rectangles with drop shadows
4. Connections should be arrows with labels if provided
5. Layout components in logical layers (frontend → backend → database)
6. Use clear, readable fonts (14-16px for component names)
7. Add subtle gradients and professional styling
8. SVG viewBox should be approximately 1000x600
9. Include proper spacing between components (80-100px)
10. Make it visually similar to professional architecture diagrams

Return ONLY the SVG code, no explanations or markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.llm_settings.claude_max_tokens,
                temperature=self.llm_settings.claude_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            svg_code = response.content[0].text.strip()

            # Clean up any markdown code blocks if present
            if "```" in svg_code:
                svg_code = svg_code.split("```")[1]
                if svg_code.startswith("svg\n") or svg_code.startswith("xml\n"):
                    svg_code = "\n".join(svg_code.split("\n")[1:])

            svg_code = svg_code.strip()

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated architecture diagram: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate architecture diagram with Claude: {e}")
            return ""

    def generate_mind_map(
        self,
        title: str,
        data: dict,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate mind map SVG using Claude.

        Args:
            title: Mind map title
            data: Mind map data with central topic and branches
            output_path: Optional path to save SVG

        Returns:
            SVG code as string
        """
        if not self.is_available():
            return ""

        central = data.get("central", "")
        branches = data.get("branches", [])

        prompt = f"""Generate a professional SVG mind map with the following specifications:

Title: {title}

Central Topic: {central}

Branches:
{json.dumps(branches, indent=2)}

Requirements:
1. Create a radial mind map with the central topic in the center
2. Branches radiate outward in a circular pattern
3. Use varying colors for different branches (use palette: #1E5D5A, #D76B38, #2E86AB, #A23B72, #F18F01)
4. Central node should be larger and prominent (ellipse with gradient)
5. Branch nodes should be rounded ellipses
6. Connect nodes with smooth curves, not straight lines
7. Use clear, readable fonts (16px for central, 12px for branches, 10px for children)
8. Add subtle drop shadows for depth
9. SVG viewBox should be approximately 1000x700
10. Make it visually appealing and professional

Return ONLY the SVG code, no explanations or markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.llm_settings.claude_max_tokens,
                temperature=self.llm_settings.claude_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            svg_code = response.content[0].text.strip()

            # Clean up any markdown code blocks
            if "```" in svg_code:
                svg_code = svg_code.split("```")[1]
                if svg_code.startswith("svg\n") or svg_code.startswith("xml\n"):
                    svg_code = "\n".join(svg_code.split("\n")[1:])

            svg_code = svg_code.strip()

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated mind map: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate mind map with Claude: {e}")
            return ""

    def generate_comparison_visual(
        self,
        title: str,
        data: dict,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate comparison table/visual SVG using Claude.

        Args:
            title: Comparison title
            data: Comparison data with items and categories
            output_path: Optional path to save SVG

        Returns:
            SVG code as string
        """
        if not self.is_available():
            return ""

        items = data.get("items", [])
        categories = data.get("categories", [])

        prompt = f"""Generate a professional SVG comparison visual with the following specifications:

Title: {title}

Items to Compare: {json.dumps(items)}

Categories with Scores:
{json.dumps(categories, indent=2)}

Requirements:
1. Create a modern comparison table/matrix
2. Header row with items across the top
3. Category names in the left column
4. Use colored bars to show scores (teal #1E5D5A, orange #D76B38, blue #2E86AB)
5. Add rounded corners to the table
6. Alternate row colors for readability (#F8F9FA and white)
7. Clear, professional typography (14px for headers, 12px for content)
8. Add subtle borders and shadows
9. SVG viewBox should fit the content (approximately 900x500)
10. Make it clean and professional like a modern dashboard

Return ONLY the SVG code, no explanations or markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.llm_settings.claude_max_tokens,
                temperature=self.llm_settings.claude_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            svg_code = response.content[0].text.strip()

            # Clean up any markdown code blocks
            if "```" in svg_code:
                svg_code = svg_code.split("```")[1]
                if svg_code.startswith("svg\n") or svg_code.startswith("xml\n"):
                    svg_code = "\n".join(svg_code.split("\n")[1:])

            svg_code = svg_code.strip()

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated comparison visual: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate comparison visual with Claude: {e}")
            return ""

    def generate_flowchart(
        self,
        title: str,
        data: dict,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate flowchart SVG using Claude.

        Args:
            title: Flowchart title
            data: Flowchart data with nodes and edges
            output_path: Optional path to save SVG

        Returns:
            SVG code as string
        """
        if not self.is_available():
            return ""

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        prompt = f"""Generate a professional SVG flowchart with the following specifications:

Title: {title}

Nodes:
{json.dumps(nodes, indent=2)}

Edges (Connections):
{json.dumps(edges, indent=2)}

Requirements:
1. Create a top-to-bottom flowchart
2. Start/End nodes: rounded rectangles with teal color (#1E5D5A)
3. Process nodes: rectangles with blue color (#2E86AB)
4. Decision nodes: diamond shapes with orange color (#D76B38)
5. Use arrows to connect nodes with labels if provided
6. Layout nodes vertically with proper spacing (100px vertical gaps)
7. Center-align nodes horizontally when possible
8. Add subtle drop shadows for depth
9. Use clear, readable fonts (13px for node text, 11px for edge labels)
10. SVG viewBox should fit content (approximately 800x1000)

Return ONLY the SVG code, no explanations or markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.llm_settings.claude_max_tokens,
                temperature=self.llm_settings.claude_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            svg_code = response.content[0].text.strip()

            # Clean up any markdown code blocks
            if "```" in svg_code:
                svg_code = svg_code.split("```")[1]
                if svg_code.startswith("svg\n") or svg_code.startswith("xml\n"):
                    svg_code = "\n".join(svg_code.split("\n")[1:])

            svg_code = svg_code.strip()

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated flowchart: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate flowchart with Claude: {e}")
            return ""

    def generate_concept_map(
        self,
        title: str,
        data: dict,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate concept map SVG using Claude.

        Args:
            title: Concept map title
            data: Concept map data with concepts and relationships
            output_path: Optional path to save SVG

        Returns:
            SVG code as string
        """
        if not self.is_available():
            return ""

        concepts = data.get("concepts", [])
        relationships = data.get("relationships", [])

        prompt = f"""Generate a professional SVG concept map with the following specifications:

Title: {title}

Concepts:
{json.dumps(concepts, indent=2)}

Relationships:
{json.dumps(relationships, indent=2)}

Requirements:
1. Create a hierarchical concept map
2. Concepts should be ellipses with varying colors by level
3. Level 0: teal (#1E5D5A), Level 1: blue (#2E86AB), Level 2: orange (#D76B38)
4. Connect concepts with dotted lines and arrows
5. Add relationship labels in italics along the connecting lines
6. Layout concepts in levels (top-level at top, children below)
7. Use clear, readable fonts (12px for concept text, 10px for relationships)
8. Add subtle drop shadows
9. SVG viewBox should fit content (approximately 900x700)
10. Make it visually clean and hierarchical

Return ONLY the SVG code, no explanations or markdown code blocks."""

        try:
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.llm_settings.claude_max_tokens,
                temperature=self.llm_settings.claude_temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            svg_code = response.content[0].text.strip()

            # Clean up any markdown code blocks
            if "```" in svg_code:
                svg_code = svg_code.split("```")[1]
                if svg_code.startswith("svg\n") or svg_code.startswith("xml\n"):
                    svg_code = "\n".join(svg_code.split("\n")[1:])

            svg_code = svg_code.strip()

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated concept map: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate concept map with Claude: {e}")
            return ""

    def _save_svg(self, svg: str, path: Path) -> None:
        """Save SVG to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        logger.debug(f"Saved Claude-generated SVG: {path}")


def generate_visualization_with_claude(
    visual_type: str,
    data: dict,
    title: str,
    output_path: Optional[Path] = None
) -> str:
    """
    Generate visualization using Claude SVG generator.

    Args:
        visual_type: "architecture", "flowchart", "comparison_visual", "concept_map", or "mind_map"
        data: Type-specific data dictionary
        title: Visualization title
        output_path: Optional path to save SVG

    Returns:
        SVG code as string
    """
    generator = ClaudeSVGGenerator()

    if not generator.is_available():
        logger.warning("Claude SVG generator not available, falling back to basic generator")
        return ""

    try:
        if visual_type == "architecture":
            return generator.generate_architecture_diagram(title, data, output_path)
        elif visual_type == "flowchart":
            return generator.generate_flowchart(title, data, output_path)
        elif visual_type == "comparison_visual":
            return generator.generate_comparison_visual(title, data, output_path)
        elif visual_type == "concept_map":
            return generator.generate_concept_map(title, data, output_path)
        elif visual_type == "mind_map":
            return generator.generate_mind_map(title, data, output_path)
        else:
            logger.warning(f"Unknown visualization type for Claude: {visual_type}")
            return ""
    except Exception as e:
        logger.error(f"Failed to generate {visual_type} with Claude: {e}")
        return ""
