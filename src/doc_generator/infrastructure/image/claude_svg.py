"""
Claude-powered SVG generator for professional diagrams.

NOTE: This module is currently DISABLED. The system uses Gemini for image generation.
Set llm.use_claude_for_visuals = true in settings.yaml to enable.

Uses Claude Sonnet 4.5 to generate high-quality SVG visualizations for
architecture diagrams, flowcharts, mind maps, and comparison visuals.
"""

import json
import math
import os
import time
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from loguru import logger

from ..observability.opik import log_llm_call
from ..settings import get_settings


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
        Invoked by: (no references found)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.settings = get_settings()
        self.llm_settings = self.settings.llm
        self.svg_max_tokens = self.llm_settings.svg_max_tokens or self.llm_settings.claude_max_tokens

        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Claude SVG generator initialized with model: {self.llm_settings.claude_model}")
        else:
            logger.warning("No Anthropic API key provided - Claude SVG generation disabled")

    def is_available(self) -> bool:
        """
        Check if Claude SVG generator is available.
        Invoked by: scripts/run_generator.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/utils/content_merger.py
        """
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
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
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
            start_time = time.perf_counter()
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.svg_max_tokens,
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
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_llm_call(
                name="svg_architecture",
                prompt=prompt,
                response=svg_code,
                provider="claude",
                model=self.llm_settings.claude_model,
                duration_ms=duration_ms,
                metadata={"title": title},
            )

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
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
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
            start_time = time.perf_counter()
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.svg_max_tokens,
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
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_llm_call(
                name="svg_mind_map",
                prompt=prompt,
                response=svg_code,
                provider="claude",
                model=self.llm_settings.claude_model,
                duration_ms=duration_ms,
                metadata={"title": title},
            )

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
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
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
            start_time = time.perf_counter()
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.svg_max_tokens,
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
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_llm_call(
                name="svg_comparison",
                prompt=prompt,
                response=svg_code,
                provider="claude",
                model=self.llm_settings.claude_model,
                duration_ms=duration_ms,
                metadata={"title": title},
            )

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
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
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
            start_time = time.perf_counter()
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.svg_max_tokens,
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
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_llm_call(
                name="svg_flowchart",
                prompt=prompt,
                response=svg_code,
                provider="claude",
                model=self.llm_settings.claude_model,
                duration_ms=duration_ms,
                metadata={"title": title},
            )

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
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
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
            start_time = time.perf_counter()
            response = self.client.messages.create(
                model=self.llm_settings.claude_model,
                max_tokens=self.svg_max_tokens,
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
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_llm_call(
                name="svg_concept_map",
                prompt=prompt,
                response=svg_code,
                provider="claude",
                model=self.llm_settings.claude_model,
                duration_ms=duration_ms,
                metadata={"title": title},
            )

            if output_path:
                self._save_svg(svg_code, output_path)

            logger.info(f"Generated concept map: {title}")
            return svg_code

        except Exception as e:
            logger.error(f"Failed to generate concept map with Claude: {e}")
            return ""

    def _save_svg(self, svg: str, path: Path) -> None:
        """
        Save SVG to file.
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        logger.debug(f"Saved Claude-generated SVG: {path}")


# Type aliases for common variations
TYPE_ALIASES = {
    "comparison": "comparison_visual",
    "diagram": "architecture",
    "chart": "comparison_visual",
    "graph": "flowchart",
    "table": "comparison_visual",
    "heatmap": "comparison_visual",
    "process": "flowchart",
    "hierarchy": "concept_map",
    "tree": "mind_map",
}


def generate_visualization_with_claude(
    visual_type: str,
    data: dict,
    title: str,
    output_path: Optional[Path] = None,
    validation_feedback: list[str] | None = None
) -> str:
    """
    Generate visualization using Claude SVG generator.

    Args:
        visual_type: "architecture", "flowchart", "comparison", "concept_map", or "mind_map"
        data: Type-specific data dictionary
        title: Visualization title
        output_path: Optional path to save SVG
        validation_feedback: Optional list of validation errors from previous attempt

    Returns:
        SVG code as string, or fallback SVG if generation fails
    Invoked by: (no references found)
    """
    generator = ClaudeSVGGenerator()

    if not generator.is_available():
        logger.warning("Claude SVG generator not available, returning fallback SVG")
        return _create_fallback_svg(visual_type, title, data)

    # Normalize type using aliases
    normalized_type = TYPE_ALIASES.get(visual_type.lower(), visual_type.lower())
    
    if normalized_type != visual_type:
        logger.debug(f"Mapped visual type '{visual_type}' to '{normalized_type}'")

    try:
        svg_content = ""
        
        if normalized_type == "architecture":
            svg_content = generator.generate_architecture_diagram(title, data, output_path)
        elif normalized_type == "flowchart":
            svg_content = generator.generate_flowchart(title, data, output_path)
        elif normalized_type == "comparison_visual":
            svg_content = generator.generate_comparison_visual(title, data, output_path)
        elif normalized_type == "concept_map":
            svg_content = generator.generate_concept_map(title, data, output_path)
        elif normalized_type == "mind_map":
            svg_content = generator.generate_mind_map(title, data, output_path)
        else:
            logger.warning(f"Unknown visualization type '{visual_type}' (normalized: '{normalized_type}'), using architecture")
            svg_content = generator.generate_architecture_diagram(title, data, output_path)
        
        # If Claude failed, return fallback
        if not svg_content:
            logger.warning(f"Claude returned empty SVG for {title}, using fallback")
            return _create_fallback_svg(normalized_type, title, data)
        
        return svg_content
        
    except Exception as e:
        logger.error(f"Failed to generate {visual_type} with Claude: {e}")
        return _create_fallback_svg(normalized_type if 'normalized_type' in dir() else "architecture", title, data)


def _create_fallback_svg(visual_type: str, title: str, data: dict) -> str:
    """
    Create a basic fallback SVG when Claude generation fails.
    
    Args:
        visual_type: Type of visualization
        title: Title for the diagram
        data: Data dictionary (used for extracting labels)
        
    Returns:
        Basic SVG code
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    # Extract some labels from data for the fallback
    labels = []
    if "components" in data:
        labels = [c.get("name", f"Item {i+1}") for i, c in enumerate(data["components"][:5])]
    elif "nodes" in data:
        labels = [n.get("text", f"Node {i+1}") for i, n in enumerate(data["nodes"][:5])]
    elif "concepts" in data:
        labels = [c.get("text", f"Concept {i+1}") for i, c in enumerate(data["concepts"][:5])]
    elif "items" in data:
        labels = data["items"][:5]
    elif "branches" in data:
        labels = [b.get("text", f"Branch {i+1}") for i, b in enumerate(data["branches"][:5])]
    
    if not labels:
        labels = ["Component 1", "Component 2", "Component 3"]
    
    # Color palette
    colors = ["#1E5D5A", "#2E86AB", "#D76B38", "#A23B72", "#F18F01"]
    
    # Build SVG based on type
    if visual_type in ("architecture", "diagram"):
        return _fallback_architecture_svg(title, labels, colors)
    elif visual_type == "flowchart":
        return _fallback_flowchart_svg(title, labels, colors)
    elif visual_type in ("comparison", "comparison_visual"):
        return _fallback_comparison_svg(title, labels, colors)
    elif visual_type == "concept_map":
        return _fallback_concept_map_svg(title, labels, colors)
    elif visual_type == "mind_map":
        return _fallback_mind_map_svg(title, labels, colors)
    else:
        return _fallback_architecture_svg(title, labels, colors)


def _fallback_architecture_svg(title: str, labels: list[str], colors: list[str]) -> str:
    """
    Generate fallback architecture diagram.
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    boxes = []
    y_offset = 80
    
    for i, label in enumerate(labels):
        color = colors[i % len(colors)]
        x = 150 + (i % 3) * 250
        y = y_offset + (i // 3) * 120
        boxes.append(f'''
        <rect x="{x}" y="{y}" width="180" height="60" rx="8" fill="{color}" opacity="0.9"/>
        <text x="{x + 90}" y="{y + 35}" text-anchor="middle" fill="white" font-size="13" font-family="Arial">{label[:20]}</text>''')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
    <rect width="800" height="400" fill="#FAFAFA"/>
    <text x="400" y="40" text-anchor="middle" font-size="18" font-weight="bold" fill="#333" font-family="Arial">{title[:50]}</text>
    {"".join(boxes)}
</svg>'''


def _fallback_flowchart_svg(title: str, labels: list[str], colors: list[str]) -> str:
    """
    Generate fallback flowchart.
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    nodes = []
    arrows = []
    
    for i, label in enumerate(labels):
        color = colors[i % len(colors)]
        y = 80 + i * 80
        nodes.append(f'''
        <rect x="300" y="{y}" width="200" height="50" rx="6" fill="{color}"/>
        <text x="400" y="{y + 30}" text-anchor="middle" fill="white" font-size="12" font-family="Arial">{label[:25]}</text>''')
        
        if i < len(labels) - 1:
            arrows.append(f'''<line x1="400" y1="{y + 50}" x2="400" y2="{y + 80}" stroke="#666" stroke-width="2" marker-end="url(#arrow)"/>''')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {100 + len(labels) * 80}">
    <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
            <path d="M0,0 L0,6 L9,3 z" fill="#666"/>
        </marker>
    </defs>
    <rect width="800" height="{100 + len(labels) * 80}" fill="#FAFAFA"/>
    <text x="400" y="40" text-anchor="middle" font-size="18" font-weight="bold" fill="#333" font-family="Arial">{title[:50]}</text>
    {"".join(arrows)}
    {"".join(nodes)}
</svg>'''


def _fallback_comparison_svg(title: str, labels: list[str], colors: list[str]) -> str:
    """
    Generate fallback comparison table.
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    rows = []
    
    for i, label in enumerate(labels):
        color = colors[i % len(colors)]
        y = 100 + i * 50
        bar_width = 150 + (i * 30) % 200
        rows.append(f'''
        <rect x="50" y="{y}" width="700" height="45" fill="{'#F8F9FA' if i % 2 == 0 else 'white'}"/>
        <text x="70" y="{y + 28}" font-size="13" fill="#333" font-family="Arial">{label[:30]}</text>
        <rect x="300" y="{y + 12}" width="{bar_width}" height="20" rx="4" fill="{color}"/>''')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {150 + len(labels) * 50}">
    <rect width="800" height="{150 + len(labels) * 50}" fill="#FAFAFA"/>
    <text x="400" y="40" text-anchor="middle" font-size="18" font-weight="bold" fill="#333" font-family="Arial">{title[:50]}</text>
    <rect x="50" y="60" width="700" height="30" fill="#E8E8E8"/>
    <text x="70" y="80" font-size="12" font-weight="bold" fill="#333" font-family="Arial">Item</text>
    <text x="420" y="80" font-size="12" font-weight="bold" fill="#333" font-family="Arial">Score</text>
    {"".join(rows)}
</svg>'''


def _fallback_concept_map_svg(title: str, labels: list[str], colors: list[str]) -> str:
    """
    Generate fallback concept map.
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    nodes = []
    lines = []
    
    # Central node
    nodes.append(f'''
    <ellipse cx="400" cy="150" rx="100" ry="40" fill="{colors[0]}"/>
    <text x="400" y="155" text-anchor="middle" fill="white" font-size="14" font-family="Arial">{title[:20]}</text>''')
    
    # Branch nodes
    for i, label in enumerate(labels[:4]):
        angle = (i * 90) - 45
        x = 400 + int(200 * math.cos(math.radians(angle)))
        y = 280 + int(80 * math.sin(math.radians(angle)))
        color = colors[(i + 1) % len(colors)]
        
        lines.append(f'<line x1="400" y1="190" x2="{x}" y2="{y - 25}" stroke="#999" stroke-width="1.5" stroke-dasharray="4"/>')
        nodes.append(f'''
        <ellipse cx="{x}" cy="{y}" rx="80" ry="30" fill="{color}"/>
        <text x="{x}" y="{y + 5}" text-anchor="middle" fill="white" font-size="11" font-family="Arial">{label[:15]}</text>''')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
    <rect width="800" height="400" fill="#FAFAFA"/>
    {"".join(lines)}
    {"".join(nodes)}
</svg>'''


def _fallback_mind_map_svg(title: str, labels: list[str], colors: list[str]) -> str:
    """
    Generate fallback mind map.
    Invoked by: src/doc_generator/infrastructure/image/claude_svg.py
    """
    nodes = []
    lines = []
    
    # Central node
    nodes.append(f'''
    <ellipse cx="400" cy="200" rx="90" ry="45" fill="{colors[0]}"/>
    <text x="400" y="205" text-anchor="middle" fill="white" font-size="14" font-weight="bold" font-family="Arial">{title[:15]}</text>''')
    
    # Branch nodes in a radial pattern
    for i, label in enumerate(labels[:6]):
        angle = (i * 60) - 30
        x = 400 + int(220 * math.cos(math.radians(angle)))
        y = 200 + int(130 * math.sin(math.radians(angle)))
        color = colors[(i + 1) % len(colors)]
        
        # Curved line
        mid_x = 400 + int(110 * math.cos(math.radians(angle)))
        mid_y = 200 + int(65 * math.sin(math.radians(angle)))
        lines.append(f'<path d="M400,200 Q{mid_x},{mid_y} {x},{y}" stroke="{color}" stroke-width="3" fill="none"/>')
        
        nodes.append(f'''
        <ellipse cx="{x}" cy="{y}" rx="70" ry="28" fill="{color}"/>
        <text x="{x}" y="{y + 5}" text-anchor="middle" fill="white" font-size="11" font-family="Arial">{label[:12]}</text>''')
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450">
    <rect width="800" height="450" fill="#FAFAFA"/>
    {"".join(lines)}
    {"".join(nodes)}
</svg>'''
