"""
SVG chart and visualization generator.

Creates professional SVG charts and diagrams for presentations and documents.
Supports: bar, pie, line, comparison charts, architecture diagrams,
flowcharts, concept maps, mind maps, and comparison visuals.
"""

import math
from pathlib import Path
from typing import Optional

from loguru import logger

from ..settings import get_settings

# Corporate color palette
_BASE_CHART_COLORS = [
    "#1E5D5A",  # Teal (primary)
    "#D76B38",  # Orange (accent)
    "#2E86AB",  # Blue
    "#A23B72",  # Magenta
    "#F18F01",  # Amber
    "#C73E1D",  # Red
    "#3A7CA5",  # Steel blue
    "#5C946E",  # Green
]

# Layer colors for architecture diagrams
_BASE_LAYER_COLORS = {
    "frontend": "#2E86AB",
    "backend": "#1E5D5A",
    "database": "#A23B72",
    "external": "#D76B38",
    "infrastructure": "#5C946E",
    "default": "#3A7CA5",
}

BACKGROUND_COLOR = "#FFFFFF"
TEXT_COLOR = "#1C1C1C"
MUTED_COLOR = "#666666"
GRID_COLOR = "#E0E0E0"
CONNECTION_COLOR = "#555555"


def _load_svg_palette() -> tuple[list[str], dict[str, str]]:
    """
    Load SVG palette settings with safe defaults.
    Invoked by: src/doc_generator/infrastructure/image/svg.py
    """
    svg_settings = get_settings().svg
    chart_colors = svg_settings.chart_colors or _BASE_CHART_COLORS
    layer_colors = dict(_BASE_LAYER_COLORS)
    layer_colors.update(svg_settings.layer_colors or {})
    return chart_colors, layer_colors


CHART_COLORS, LAYER_COLORS = _load_svg_palette()


class SVGGenerator:
    """
    Generate professional SVG charts for presentations.
    """

    def __init__(self, width: int | None = None, height: int | None = None):
        """
        Initialize SVG generator.

        Args:
            width: Chart width in pixels
            height: Chart height in pixels
        Invoked by: (no references found)
        """
        svg_settings = get_settings().svg
        self.width = width if width is not None else svg_settings.default_width
        self.height = height if height is not None else svg_settings.default_height
        self.padding = 60
        self.font_family = "Arial, Helvetica, sans-serif"

    def generate_bar_chart(
        self,
        data: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate horizontal bar chart.

        Args:
            data: List of {label, value} dictionaries
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        if not data:
            return ""

        chart_width = self.width - 2 * self.padding - 100  # Extra space for labels
        chart_height = self.height - 2 * self.padding - 40  # Space for title

        max_value = max(d.get("value", 0) for d in data)
        if max_value == 0:
            max_value = 1

        bar_height = min(40, (chart_height - 20) / len(data) - 10)
        spacing = (chart_height - bar_height * len(data)) / (len(data) + 1)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',  # noqa: E501
            f'<rect width="{self.width}" height="{self.height}" fill="{BACKGROUND_COLOR}"/>',
            # Title
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="24" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Draw bars
        y_start = self.padding + 40
        x_start = self.padding + 100  # Space for labels

        for i, item in enumerate(data):
            label = item.get("label", f"Item {i+1}")
            value = item.get("value", 0)
            bar_width = (value / max_value) * chart_width
            y = y_start + spacing + i * (bar_height + spacing)
            color = CHART_COLORS[i % len(CHART_COLORS)]

            # Label
            svg_parts.append(
                f'<text x="{x_start - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" font-family="{self.font_family}" font-size="14" fill="{TEXT_COLOR}">{self._escape(str(label))}</text>'  # noqa: E501
            )

            # Bar with rounded corners
            svg_parts.append(
                f'<rect x="{x_start}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" ry="4"/>'
            )

            # Value label
            svg_parts.append(
                f'<text x="{x_start + bar_width + 10}" y="{y + bar_height/2 + 5}" font-family="{self.font_family}" font-size="14" font-weight="bold" fill="{TEXT_COLOR}">{value}</text>'  # noqa: E501
            )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_pie_chart(
        self,
        data: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate pie chart.

        Args:
            data: List of {label, value} dictionaries
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        if not data:
            return ""

        total = sum(d.get("value", 0) for d in data)
        if total == 0:
            total = 1

        cx = self.width / 2 - 80
        cy = self.height / 2 + 20
        radius = min(self.width, self.height) / 3

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',  # noqa: E501
            f'<rect width="{self.width}" height="{self.height}" fill="{BACKGROUND_COLOR}"/>',
            # Title
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="24" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Draw pie slices
        start_angle = -90  # Start from top
        for i, item in enumerate(data):
            value = item.get("value", 0)
            percentage = value / total
            angle = percentage * 360
            end_angle = start_angle + angle

            # Calculate path
            path = self._pie_slice_path(cx, cy, radius, start_angle, end_angle)
            color = CHART_COLORS[i % len(CHART_COLORS)]

            svg_parts.append(f'<path d="{path}" fill="{color}" stroke="{BACKGROUND_COLOR}" stroke-width="2"/>')

            start_angle = end_angle

        # Legend
        legend_x = self.width - 160
        legend_y = 80

        for i, item in enumerate(data):
            label = item.get("label", f"Item {i+1}")
            value = item.get("value", 0)
            percentage = (value / total) * 100
            color = CHART_COLORS[i % len(CHART_COLORS)]
            y = legend_y + i * 28

            # Color box
            svg_parts.append(
                f'<rect x="{legend_x}" y="{y}" width="16" height="16" fill="{color}" rx="2"/>'
            )
            # Label
            svg_parts.append(
                f'<text x="{legend_x + 24}" y="{y + 13}" font-family="{self.font_family}" font-size="13" fill="{TEXT_COLOR}">{self._escape(str(label))} ({percentage:.0f}%)</text>'  # noqa: E501
            )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_comparison_chart(
        self,
        data: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate comparison/column chart.

        Args:
            data: List of {label, value} dictionaries
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        if not data:
            return ""

        chart_width = self.width - 2 * self.padding
        chart_height = self.height - 2 * self.padding - 60

        max_value = max(d.get("value", 0) for d in data)
        if max_value == 0:
            max_value = 1

        bar_width = min(60, (chart_width - 40) / len(data) - 20)
        spacing = (chart_width - bar_width * len(data)) / (len(data) + 1)

        x_start = self.padding
        y_bottom = self.height - self.padding - 30

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',  # noqa: E501
            f'<rect width="{self.width}" height="{self.height}" fill="{BACKGROUND_COLOR}"/>',
            # Title
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="24" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
            # Baseline
            f'<line x1="{x_start}" y1="{y_bottom}" x2="{x_start + chart_width}" y2="{y_bottom}" stroke="{GRID_COLOR}" stroke-width="2"/>',  # noqa: E501
        ]

        # Grid lines
        for i in range(5):
            y = y_bottom - (i / 4) * chart_height
            value = (i / 4) * max_value
            svg_parts.append(
                f'<line x1="{x_start}" y1="{y}" x2="{x_start + chart_width}" y2="{y}" stroke="{GRID_COLOR}" stroke-width="1" stroke-dasharray="4"/>'  # noqa: E501
            )
            svg_parts.append(
                f'<text x="{x_start - 10}" y="{y + 5}" text-anchor="end" font-family="{self.font_family}" font-size="12" fill="{MUTED_COLOR}">{value:.0f}</text>'  # noqa: E501
            )

        # Draw columns
        for i, item in enumerate(data):
            label = item.get("label", f"Item {i+1}")
            value = item.get("value", 0)
            bar_height = (value / max_value) * chart_height
            x = x_start + spacing + i * (bar_width + spacing)
            y = y_bottom - bar_height
            color = CHART_COLORS[i % len(CHART_COLORS)]

            # Column
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{color}" rx="4" ry="4"/>'
            )

            # Value on top
            svg_parts.append(
                f'<text x="{x + bar_width/2}" y="{y - 8}" text-anchor="middle" font-family="{self.font_family}" font-size="14" font-weight="bold" fill="{TEXT_COLOR}">{value}</text>'  # noqa: E501
            )

            # Label below
            svg_parts.append(
                f'<text x="{x + bar_width/2}" y="{y_bottom + 20}" text-anchor="middle" font-family="{self.font_family}" font-size="12" fill="{TEXT_COLOR}">{self._escape(str(label))}</text>'  # noqa: E501
            )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_line_chart(
        self,
        data: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate line chart.

        Args:
            data: List of {label, value} dictionaries
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        if not data or len(data) < 2:
            return ""

        chart_width = self.width - 2 * self.padding - 40
        chart_height = self.height - 2 * self.padding - 60

        max_value = max(d.get("value", 0) for d in data)
        min_value = min(d.get("value", 0) for d in data)
        if max_value == min_value:
            max_value = min_value + 1

        x_start = self.padding + 40
        y_bottom = self.height - self.padding - 30

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',  # noqa: E501
            f'<rect width="{self.width}" height="{self.height}" fill="{BACKGROUND_COLOR}"/>',
            # Title
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="24" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
            # Axes
            f'<line x1="{x_start}" y1="{y_bottom}" x2="{x_start + chart_width}" y2="{y_bottom}" stroke="{TEXT_COLOR}" stroke-width="2"/>',  # noqa: E501
            f'<line x1="{x_start}" y1="{y_bottom}" x2="{x_start}" y2="{y_bottom - chart_height}" stroke="{TEXT_COLOR}" stroke-width="2"/>',  # noqa: E501
        ]

        # Calculate points
        points = []
        x_step = chart_width / (len(data) - 1)

        for i, item in enumerate(data):
            value = item.get("value", 0)
            x = x_start + i * x_step
            y = y_bottom - ((value - min_value) / (max_value - min_value)) * chart_height
            points.append((x, y))

        # Draw area under line
        area_path = f"M {points[0][0]} {y_bottom}"
        for x, y in points:
            area_path += f" L {x} {y}"
        area_path += f" L {points[-1][0]} {y_bottom} Z"
        svg_parts.append(f'<path d="{area_path}" fill="{CHART_COLORS[0]}" fill-opacity="0.2"/>')

        # Draw line
        line_path = f"M {points[0][0]} {points[0][1]}"
        for x, y in points[1:]:
            line_path += f" L {x} {y}"
        svg_parts.append(f'<path d="{line_path}" stroke="{CHART_COLORS[0]}" stroke-width="3" fill="none"/>')

        # Draw points and labels
        for i, (x, y) in enumerate(points):
            label = data[i].get("label", f"{i+1}")
            value = data[i].get("value", 0)

            # Point
            svg_parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{CHART_COLORS[0]}" stroke="{BACKGROUND_COLOR}" stroke-width="2"/>')  # noqa: E501

            # X-axis label
            svg_parts.append(
                f'<text x="{x}" y="{y_bottom + 18}" text-anchor="middle" font-family="{self.font_family}" font-size="11" fill="{TEXT_COLOR}">{self._escape(str(label))}</text>'  # noqa: E501
            )

        # Y-axis labels
        for i in range(5):
            y = y_bottom - (i / 4) * chart_height
            value = min_value + (i / 4) * (max_value - min_value)
            svg_parts.append(
                f'<text x="{x_start - 8}" y="{y + 4}" text-anchor="end" font-family="{self.font_family}" font-size="11" fill="{MUTED_COLOR}">{value:.0f}</text>'  # noqa: E501
            )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_architecture_diagram(
        self,
        components: list[dict],
        connections: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate architecture diagram with components and connections.

        Args:
            components: List of {"id", "name", "layer"} dictionaries
            connections: List of {"from", "to", "label"} dictionaries
            title: Diagram title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        if not components:
            return ""

        # Calculate layout
        component_width = 140
        component_height = 60
        h_spacing = 60
        v_spacing = 80

        # Group by layer
        layers = {}
        for comp in components:
            layer = comp.get("layer", "default")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(comp)

        layer_order = ["frontend", "backend", "database", "external", "infrastructure", "default"]
        sorted_layers = [layer_name for layer_name in layer_order if layer_name in layers]  # noqa: E501
        for layer_name in layers:  # noqa: E501
            if layer_name not in sorted_layers:
                sorted_layers.append(layer_name)

        # Calculate positions
        positions = {}
        y_offset = 80
        max_width = 0

        for layer in sorted_layers:
            layer_components = layers[layer]
            total_width = len(layer_components) * component_width + (len(layer_components) - 1) * h_spacing
            x_start = (self.width - total_width) / 2

            for i, comp in enumerate(layer_components):
                x = x_start + i * (component_width + h_spacing)
                positions[comp["id"]] = {
                    "x": x,
                    "y": y_offset,
                    "cx": x + component_width / 2,
                    "cy": y_offset + component_height / 2,
                    "layer": layer,
                    "name": comp.get("name", f"Component {comp['id']}")
                }
            max_width = max(max_width, total_width)
            y_offset += component_height + v_spacing

        # Adjust height if needed
        total_height = max(self.height, y_offset + 40)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {total_height}" width="{self.width}" height="{total_height}">',  # noqa: E501
            # Definitions for shadows and gradients
            '<defs>',
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.15"/>',
            '</filter>',
            '</defs>',
            f'<rect width="{self.width}" height="{total_height}" fill="{BACKGROUND_COLOR}"/>',
            # Title
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="22" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Draw connections first (behind components)
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            label = conn.get("label", "")

            if from_id in positions and to_id in positions:
                from_pos = positions[from_id]
                to_pos = positions[to_id]

                # Calculate connection points
                if from_pos["cy"] < to_pos["cy"]:
                    # Top to bottom
                    x1, y1 = from_pos["cx"], from_pos["y"] + component_height
                    x2, y2 = to_pos["cx"], to_pos["y"]
                elif from_pos["cy"] > to_pos["cy"]:
                    # Bottom to top
                    x1, y1 = from_pos["cx"], from_pos["y"]
                    x2, y2 = to_pos["cx"], to_pos["y"] + component_height
                elif from_pos["cx"] < to_pos["cx"]:
                    # Left to right
                    x1, y1 = from_pos["x"] + component_width, from_pos["cy"]
                    x2, y2 = to_pos["x"], to_pos["cy"]
                else:
                    # Right to left
                    x1, y1 = from_pos["x"], from_pos["cy"]
                    x2, y2 = to_pos["x"] + component_width, to_pos["cy"]

                # Draw arrow line
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{CONNECTION_COLOR}" stroke-width="2" marker-end="url(#arrowhead)"/>'  # noqa: E501
                )

                # Add label if present
                if label:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    svg_parts.append(
                        f'<rect x="{mid_x - 25}" y="{mid_y - 10}" width="50" height="16" fill="{BACKGROUND_COLOR}" rx="3"/>'  # noqa: E501
                    )
                    svg_parts.append(
                        f'<text x="{mid_x}" y="{mid_y + 3}" text-anchor="middle" font-family="{self.font_family}" font-size="10" fill="{MUTED_COLOR}">{self._escape(label)}</text>'  # noqa: E501
                    )

        # Add arrowhead marker
        svg_parts.insert(3, '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">')  # noqa: E501
        svg_parts.insert(4, f'<polygon points="0 0, 10 3.5, 0 7" fill="{CONNECTION_COLOR}"/>')
        svg_parts.insert(5, '</marker>')

        # Draw components
        for comp_id, pos in positions.items():
            layer = pos["layer"]
            color = LAYER_COLORS.get(layer, LAYER_COLORS["default"])
            name = pos["name"]

            # Component box with shadow
            svg_parts.append(
                f'<rect x="{pos["x"]}" y="{pos["y"]}" width="{component_width}" height="{component_height}" '
                f'fill="{color}" rx="8" ry="8" filter="url(#shadow)"/>'
            )

            # Component name (wrap if needed)
            wrapped_name = self._wrap_text(name, 16)
            for i, line in enumerate(wrapped_name[:2]):
                y_text = pos["cy"] + (i - (len(wrapped_name[:2]) - 1) / 2) * 16
                svg_parts.append(
                    f'<text x="{pos["cx"]}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{self.font_family}" font-size="13" font-weight="500" fill="white">{self._escape(line)}</text>'  # noqa: E501
                )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_flowchart(
        self,
        nodes: list[dict],
        edges: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate flowchart with process nodes and decision diamonds.

        Args:
            nodes: List of {"id", "type", "text"} where type is start/end/process/decision
            edges: List of {"from", "to", "label"} dictionaries
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        if not nodes:
            return ""

        node_width = 140
        node_height = 50
        diamond_size = 60
        v_spacing = 60
        h_spacing = 80

        # Build adjacency for layout
        children = {n["id"]: [] for n in nodes}
        for edge in edges:
            if edge["from"] in children:
                children[edge["from"]].append(edge["to"])

        # Simple top-down layout
        positions = {}
        visited = set()
        levels = {}

        def assign_level(node_id, level):
            """
            Invoked by: src/doc_generator/infrastructure/image/svg.py
            """
            if node_id in visited:
                return
            visited.add(node_id)
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)
            for child in children.get(node_id, []):
                assign_level(child, level + 1)

        # Find start node or first node
        start_nodes = [n["id"] for n in nodes if n.get("type") == "start"]
        if not start_nodes:
            start_nodes = [nodes[0]["id"]]

        for start in start_nodes:
            assign_level(start, 0)

        # Assign any unvisited nodes
        for n in nodes:
            if n["id"] not in visited:
                max_level = max(levels.keys()) + 1 if levels else 0
                assign_level(n["id"], max_level)

        # Calculate positions
        y_offset = 80
        node_map = {n["id"]: n for n in nodes}

        for level in sorted(levels.keys()):
            level_nodes = levels[level]
            total_width = len(level_nodes) * node_width + (len(level_nodes) - 1) * h_spacing
            x_start = (self.width - total_width) / 2

            for i, node_id in enumerate(level_nodes):
                x = x_start + i * (node_width + h_spacing)
                node = node_map[node_id]
                positions[node_id] = {
                    "x": x,
                    "y": y_offset,
                    "cx": x + node_width / 2,
                    "cy": y_offset + node_height / 2,
                    "type": node.get("type", "process"),
                    "text": node.get("text", "")
                }
            y_offset += node_height + v_spacing

        total_height = max(self.height, y_offset + 40)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {total_height}" width="{self.width}" height="{total_height}">',  # noqa: E501
            '<defs>',
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.15"/>',
            '</filter>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
            f'<polygon points="0 0, 10 3.5, 0 7" fill="{CONNECTION_COLOR}"/>',
            '</marker>',
            '</defs>',
            f'<rect width="{self.width}" height="{total_height}" fill="{BACKGROUND_COLOR}"/>',
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="22" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Draw edges
        for edge in edges:
            from_id = edge.get("from")
            to_id = edge.get("to")
            label = edge.get("label", "")

            if from_id in positions and to_id in positions:
                from_pos = positions[from_id]
                to_pos = positions[to_id]

                x1, y1 = from_pos["cx"], from_pos["y"] + node_height
                x2, y2 = to_pos["cx"], to_pos["y"]

                # Curved path for non-direct connections
                if abs(x1 - x2) > 10:
                    mid_y = (y1 + y2) / 2
                    path = f"M {x1} {y1} C {x1} {mid_y}, {x2} {mid_y}, {x2} {y2}"
                    svg_parts.append(f'<path d="{path}" stroke="{CONNECTION_COLOR}" stroke-width="2" fill="none" marker-end="url(#arrowhead)"/>')  # noqa: E501
                else:
                    svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{CONNECTION_COLOR}" stroke-width="2" marker-end="url(#arrowhead)"/>')  # noqa: E501

                if label:
                    mid_x = (x1 + x2) / 2 + 30
                    mid_y = (y1 + y2) / 2
                    svg_parts.append(f'<text x="{mid_x}" y="{mid_y}" font-family="{self.font_family}" font-size="11" fill="{MUTED_COLOR}">{self._escape(label)}</text>')  # noqa: E501

        # Draw nodes
        for node_id, pos in positions.items():
            node_type = pos["type"]
            text = pos["text"]
            cx, cy = pos["cx"], pos["cy"]

            if node_type == "start" or node_type == "end":
                # Oval/rounded rectangle
                color = CHART_COLORS[0] if node_type == "start" else CHART_COLORS[5]
                svg_parts.append(
                    f'<rect x="{pos["x"]}" y="{pos["y"]}" width="{node_width}" height="{node_height}" '
                    f'fill="{color}" rx="25" ry="25" filter="url(#shadow)"/>'
                )
            elif node_type == "decision":
                # Diamond shape
                color = CHART_COLORS[1]
                points = f"{cx},{pos['y']} {cx+diamond_size},{cy} {cx},{pos['y']+node_height} {cx-diamond_size},{cy}"
                svg_parts.append(f'<polygon points="{points}" fill="{color}" filter="url(#shadow)"/>')
            else:
                # Rectangle for process
                color = CHART_COLORS[2]
                svg_parts.append(
                    f'<rect x="{pos["x"]}" y="{pos["y"]}" width="{node_width}" height="{node_height}" '
                    f'fill="{color}" rx="8" ry="8" filter="url(#shadow)"/>'
                )

            # Text
            wrapped = self._wrap_text(text, 18)
            for i, line in enumerate(wrapped[:2]):
                y_text = cy + (i - (len(wrapped[:2]) - 1) / 2) * 14
                svg_parts.append(
                    f'<text x="{cx}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{self.font_family}" font-size="12" fill="white">{self._escape(line)}</text>'  # noqa: E501
                )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_comparison_visual(
        self,
        items: list[str],
        categories: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate comparison visual with items and category scores.

        Args:
            items: List of item names to compare
            categories: List of {"name", "scores"} where scores match items length
            title: Chart title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        if not items or not categories:
            return ""

        # Layout constants
        header_height = 50
        row_height = 40
        col_width = 100
        label_col_width = 120

        num_cols = len(items)
        num_rows = len(categories)
        table_width = label_col_width + num_cols * col_width
        table_height = header_height + num_rows * row_height

        x_start = (self.width - table_width) / 2
        y_start = 70

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {y_start + table_height + 40}" width="{self.width}" height="{y_start + table_height + 40}">',  # noqa: E501
            f'<rect width="{self.width}" height="{y_start + table_height + 40}" fill="{BACKGROUND_COLOR}"/>',
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="22" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Header row
        svg_parts.append(
            f'<rect x="{x_start}" y="{y_start}" width="{table_width}" height="{header_height}" fill="{CHART_COLORS[0]}" rx="8" ry="8"/>'  # noqa: E501
        )
        svg_parts.append(
            f'<text x="{x_start + label_col_width/2}" y="{y_start + header_height/2 + 5}" text-anchor="middle" '
            f'font-family="{self.font_family}" font-size="13" font-weight="bold" fill="white">Category</text>'  # noqa: E501
        )

        for i, item in enumerate(items):
            x = x_start + label_col_width + i * col_width + col_width / 2
            wrapped = self._wrap_text(item, 12)
            svg_parts.append(
                f'<text x="{x}" y="{y_start + header_height/2 + 5}" text-anchor="middle" '
                f'font-family="{self.font_family}" font-size="12" font-weight="bold" fill="white">{self._escape(wrapped[0])}</text>'  # noqa: E501
            )

        # Data rows
        for row_idx, category in enumerate(categories):
            y = y_start + header_height + row_idx * row_height
            bg_color = "#F8F9FA" if row_idx % 2 == 0 else BACKGROUND_COLOR

            svg_parts.append(
                f'<rect x="{x_start}" y="{y}" width="{table_width}" height="{row_height}" fill="{bg_color}"/>'
            )

            # Category name
            svg_parts.append(
                f'<text x="{x_start + 10}" y="{y + row_height/2 + 5}" '
                f'font-family="{self.font_family}" font-size="12" font-weight="500" fill="{TEXT_COLOR}">{self._escape(category.get("name", ""))}</text>'  # noqa: E501
            )

            # Scores as visual indicators
            scores = category.get("scores", [])
            max_score = max(scores) if scores else 1
            for i, score in enumerate(scores):
                x = x_start + label_col_width + i * col_width + 10
                bar_width = (score / max_score) * (col_width - 30)
                color_idx = i % len(CHART_COLORS)

                svg_parts.append(
                    f'<rect x="{x}" y="{y + 10}" width="{bar_width}" height="{row_height - 20}" '
                    f'fill="{CHART_COLORS[color_idx]}" rx="4" ry="4"/>'
                )
                svg_parts.append(
                    f'<text x="{x + bar_width + 5}" y="{y + row_height/2 + 4}" '
                    f'font-family="{self.font_family}" font-size="11" fill="{TEXT_COLOR}">{score}</text>'  # noqa: E501
                )

        # Border
        svg_parts.append(
            f'<rect x="{x_start}" y="{y_start}" width="{table_width}" height="{header_height + num_rows * row_height}" '
            f'fill="none" stroke="{GRID_COLOR}" stroke-width="1" rx="8" ry="8"/>'
        )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_concept_map(
        self,
        concepts: list[dict],
        relationships: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate concept map with hierarchical concepts and relationships.

        Args:
            concepts: List of {"id", "text", "level"} dictionaries
            relationships: List of {"from", "to", "label"} dictionaries
            title: Map title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        if not concepts:
            return ""

        # Group by level
        levels = {}
        for concept in concepts:
            level = concept.get("level", 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(concept)

        # Calculate positions
        positions = {}
        node_width = 120
        node_height = 45
        h_spacing = 40
        v_spacing = 70
        y_offset = 80

        for level in sorted(levels.keys()):
            level_concepts = levels[level]
            total_width = len(level_concepts) * node_width + (len(level_concepts) - 1) * h_spacing
            x_start = (self.width - total_width) / 2

            for i, concept in enumerate(level_concepts):
                x = x_start + i * (node_width + h_spacing)
                positions[concept["id"]] = {
                    "x": x,
                    "y": y_offset,
                    "cx": x + node_width / 2,
                    "cy": y_offset + node_height / 2,
                    "text": concept.get("text", ""),
                    "level": level
                }
            y_offset += node_height + v_spacing

        total_height = max(self.height, y_offset + 40)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {total_height}" width="{self.width}" height="{total_height}">',  # noqa: E501
            '<defs>',
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="2" dy="2" stdDeviation="2" flood-opacity="0.1"/>',
            '</filter>',
            '<marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">',
            f'<polygon points="0 0, 8 3, 0 6" fill="{MUTED_COLOR}"/>',
            '</marker>',
            '</defs>',
            f'<rect width="{self.width}" height="{total_height}" fill="{BACKGROUND_COLOR}"/>',
            f'<text x="{self.width/2}" y="35" text-anchor="middle" font-family="{self.font_family}" font-size="22" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        # Draw relationships
        for rel in relationships:
            from_id = rel.get("from")
            to_id = rel.get("to")
            label = rel.get("label", "")

            if from_id in positions and to_id in positions:
                from_pos = positions[from_id]
                to_pos = positions[to_id]

                x1, y1 = from_pos["cx"], from_pos["y"] + node_height
                x2, y2 = to_pos["cx"], to_pos["y"]

                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED_COLOR}" '
                    f'stroke-width="1.5" stroke-dasharray="4" marker-end="url(#arrowhead)"/>'
                )

                if label:
                    mid_x = (x1 + x2) / 2
                    mid_y = (y1 + y2) / 2
                    svg_parts.append(
                        f'<text x="{mid_x + 5}" y="{mid_y}" font-family="{self.font_family}" '
                        f'font-size="10" font-style="italic" fill="{MUTED_COLOR}">{self._escape(label)}</text>'  # noqa: E501
                    )

        # Draw concepts
        for concept_id, pos in positions.items():
            level = pos["level"]
            text = pos["text"]

            # Color based on level
            color = CHART_COLORS[level % len(CHART_COLORS)]

            # Ellipse shape for concepts
            rx = node_width / 2
            ry = node_height / 2
            svg_parts.append(
                f'<ellipse cx="{pos["cx"]}" cy="{pos["cy"]}" rx="{rx}" ry="{ry}" '
                f'fill="{color}" filter="url(#shadow)"/>'
            )

            # Text
            wrapped = self._wrap_text(text, 14)
            for i, line in enumerate(wrapped[:2]):
                y_text = pos["cy"] + (i - (len(wrapped[:2]) - 1) / 2) * 14
                svg_parts.append(
                    f'<text x="{pos["cx"]}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{self.font_family}" font-size="11" fill="white">{self._escape(line)}</text>'  # noqa: E501
                )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def generate_mind_map(
        self,
        central: str,
        branches: list[dict],
        title: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate mind map with central concept and radiating branches.

        Args:
            central: Central concept text
            branches: List of {"text", "children"} dictionaries
            title: Map title
            output_path: Optional path to save SVG

        Returns:
            SVG string
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        if not central:
            return ""

        cx, cy = self.width / 2, self.height / 2 + 20
        central_rx, central_ry = 80, 40
        branch_rx, branch_ry = 60, 25
        child_rx, child_ry = 50, 20

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" width="{self.width}" height="{self.height}">',  # noqa: E501
            '<defs>',
            '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
            '<feDropShadow dx="2" dy="2" stdDeviation="3" flood-opacity="0.15"/>',
            '</filter>',
            '</defs>',
            f'<rect width="{self.width}" height="{self.height}" fill="{BACKGROUND_COLOR}"/>',
            f'<text x="{self.width/2}" y="30" text-anchor="middle" font-family="{self.font_family}" font-size="20" font-weight="bold" fill="{TEXT_COLOR}">{self._escape(title)}</text>',  # noqa: E501
        ]

        num_branches = len(branches)
        if num_branches == 0:
            # Just central node
            svg_parts.append(
                f'<ellipse cx="{cx}" cy="{cy}" rx="{central_rx}" ry="{central_ry}" fill="{CHART_COLORS[0]}" filter="url(#shadow)"/>'  # noqa: E501
            )
            wrapped = self._wrap_text(central, 12)
            for i, line in enumerate(wrapped[:2]):
                y_text = cy + (i - (len(wrapped[:2]) - 1) / 2) * 16
                svg_parts.append(
                    f'<text x="{cx}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{self.font_family}" font-size="14" font-weight="bold" fill="white">{self._escape(line)}</text>'  # noqa: E501
                )
            svg_parts.append('</svg>')
            return '\n'.join(svg_parts)

        # Calculate branch positions in a radial layout
        angle_step = 360 / num_branches
        branch_distance = 180

        branch_positions = []
        for i, branch in enumerate(branches):
            angle = math.radians(i * angle_step - 90)  # Start from top
            bx = cx + branch_distance * math.cos(angle)
            by = cy + branch_distance * math.sin(angle)
            branch_positions.append({
                "x": bx,
                "y": by,
                "angle": angle,
                "text": branch.get("text", ""),
                "children": branch.get("children", [])
            })

        # Draw connections from center to branches
        for bp in branch_positions:
            svg_parts.append(
                f'<line x1="{cx}" y1="{cy}" x2="{bp["x"]}" y2="{bp["y"]}" stroke="{MUTED_COLOR}" stroke-width="2"/>'
            )

        # Draw child connections and nodes
        child_distance = 80
        for idx, bp in enumerate(branch_positions):
            children = bp["children"]
            if children:
                num_children = len(children)
                base_angle = bp["angle"]
                spread = math.radians(40)  # Spread angle for children

                for j, child in enumerate(children):
                    if num_children == 1:
                        child_angle = base_angle
                    else:
                        child_angle = base_angle + spread * (j - (num_children - 1) / 2)

                    child_x = bp["x"] + child_distance * math.cos(child_angle)
                    child_y = bp["y"] + child_distance * math.sin(child_angle)

                    # Connection line
                    svg_parts.append(
                        f'<line x1="{bp["x"]}" y1="{bp["y"]}" x2="{child_x}" y2="{child_y}" stroke="{MUTED_COLOR}" stroke-width="1.5"/>'  # noqa: E501
                    )

                    # Child node
                    color = CHART_COLORS[(idx + j + 2) % len(CHART_COLORS)]
                    svg_parts.append(
                        f'<ellipse cx="{child_x}" cy="{child_y}" rx="{child_rx}" ry="{child_ry}" fill="{color}" filter="url(#shadow)"/>'  # noqa: E501
                    )

                    # Child text
                    child_text = child if isinstance(child, str) else child.get("text", "")
                    wrapped = self._wrap_text(child_text, 10)
                    svg_parts.append(
                        f'<text x="{child_x}" y="{child_y + 4}" text-anchor="middle" dominant-baseline="middle" '
                        f'font-family="{self.font_family}" font-size="10" fill="white">{self._escape(wrapped[0])}</text>'  # noqa: E501
                    )

        # Draw branch nodes
        for idx, bp in enumerate(branch_positions):
            color = CHART_COLORS[(idx + 1) % len(CHART_COLORS)]
            svg_parts.append(
                f'<ellipse cx="{bp["x"]}" cy="{bp["y"]}" rx="{branch_rx}" ry="{branch_ry}" fill="{color}" filter="url(#shadow)"/>'  # noqa: E501
            )
            wrapped = self._wrap_text(bp["text"], 10)
            for i, line in enumerate(wrapped[:2]):
                y_text = bp["y"] + (i - (len(wrapped[:2]) - 1) / 2) * 12
                svg_parts.append(
                    f'<text x="{bp["x"]}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                    f'font-family="{self.font_family}" font-size="11" font-weight="500" fill="white">{self._escape(line)}</text>'  # noqa: E501
                )

        # Draw central node (on top)
        svg_parts.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{central_rx}" ry="{central_ry}" fill="{CHART_COLORS[0]}" filter="url(#shadow)"/>'  # noqa: E501
        )
        wrapped = self._wrap_text(central, 12)
        for i, line in enumerate(wrapped[:2]):
            y_text = cy + (i - (len(wrapped[:2]) - 1) / 2) * 16
            svg_parts.append(
                f'<text x="{cx}" y="{y_text}" text-anchor="middle" dominant-baseline="middle" '
                f'font-family="{self.font_family}" font-size="14" font-weight="bold" fill="white">{self._escape(line)}</text>'  # noqa: E501
            )

        svg_parts.append('</svg>')
        svg = '\n'.join(svg_parts)

        if output_path:
            self._save_svg(svg, output_path)

        return svg

    def _wrap_text(self, text: str, max_chars: int) -> list[str]:
        """
        Wrap text to fit within max characters per line.

        Args:
            text: Text to wrap
            max_chars: Maximum characters per line

        Returns:
            List of text lines
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        if len(text) <= max_chars:
            return [text]

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word[:max_chars]  # Truncate long words

        if current_line:
            lines.append(current_line)

        return lines if lines else [text[:max_chars] + "..."]

    def _pie_slice_path(self, cx: float, cy: float, r: float, start_angle: float, end_angle: float) -> str:
        """
        Calculate SVG path for pie slice.
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        import math

        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)

        large_arc = 1 if (end_angle - start_angle) > 180 else 0

        return f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"

    def _escape(self, text: str) -> str:
        """
        Escape text for SVG.
        Invoked by: src/doc_generator/infrastructure/image/svg.py
        """
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    def _save_svg(self, svg: str, path: Path) -> None:
        """
        Save SVG to file.
        Invoked by: src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/svg.py
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
        logger.debug(f"Saved SVG chart: {path}")


def generate_chart(
    chart_type: str,
    data: list[dict],
    title: str,
    output_path: Optional[Path] = None,
    width: int = 800,
    height: int = 500
) -> str:
    """
    Generate chart based on type.

    Args:
        chart_type: "bar", "pie", "line", or "comparison"
        data: List of {label, value} dictionaries
        title: Chart title
        output_path: Optional path to save SVG
        width: Chart width
        height: Chart height

    Returns:
        SVG string
    Invoked by: (no references found)
    """
    generator = SVGGenerator(width=width, height=height)

    chart_methods = {
        "bar": generator.generate_bar_chart,
        "pie": generator.generate_pie_chart,
        "line": generator.generate_line_chart,
        "comparison": generator.generate_comparison_chart,
    }

    method = chart_methods.get(chart_type, generator.generate_bar_chart)
    return method(data, title, output_path)


def generate_visualization(
    visual_type: str,
    data: dict,
    title: str,
    output_path: Optional[Path] = None,
    width: int = 800,
    height: int = 500
) -> str:
    """
    Generate visualization based on type.

    Args:
        visual_type: "architecture", "flowchart", "comparison_visual", "concept_map", or "mind_map"
        data: Type-specific data dictionary
        title: Visualization title
        output_path: Optional path to save SVG
        width: SVG width
        height: SVG height

    Returns:
        SVG string
    Invoked by: (no references found)
    """
    generator = SVGGenerator(width=width, height=height)

    try:
        if visual_type == "architecture":
            components = data.get("components", [])
            connections = data.get("connections", [])
            return generator.generate_architecture_diagram(components, connections, title, output_path)

        elif visual_type == "flowchart":
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            return generator.generate_flowchart(nodes, edges, title, output_path)

        elif visual_type == "comparison_visual":
            items = data.get("items", [])
            categories = data.get("categories", [])
            return generator.generate_comparison_visual(items, categories, title, output_path)

        elif visual_type == "concept_map":
            concepts = data.get("concepts", [])
            relationships = data.get("relationships", [])
            return generator.generate_concept_map(concepts, relationships, title, output_path)

        elif visual_type == "mind_map":
            central = data.get("central", "")
            branches = data.get("branches", [])
            return generator.generate_mind_map(central, branches, title, output_path)

        else:
            logger.warning(f"Unknown visualization type: {visual_type}")
            return ""

    except Exception as e:
        logger.error(f"Failed to generate {visual_type} visualization: {e}")
        return ""
