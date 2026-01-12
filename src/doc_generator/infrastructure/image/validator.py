"""
SVG Validator for checking generated SVG code quality.

Validates:
1. SVG syntax and structure
2. Text element overlaps
3. Shape/element overlaps
4. Bounding box issues
5. Missing required attributes
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger


@dataclass
class BoundingBox:
    """Represents a bounding box for overlap detection."""
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        """
        Invoked by: src/doc_generator/infrastructure/image/svg.py, src/doc_generator/infrastructure/image/validator.py
        """
        return self.x + self.width

    @property
    def y2(self) -> float:
        """
        Invoked by: src/doc_generator/infrastructure/image/svg.py, src/doc_generator/infrastructure/image/validator.py
        """
        return self.y + self.height

    def overlaps(self, other: "BoundingBox", threshold: float = 0.5) -> bool:
        """
        Check if this bounding box overlaps with another.

        Args:
            other: Another bounding box
            threshold: Overlap ratio threshold (0-1)

        Returns:
            True if overlap exceeds threshold
        Invoked by: .claude/skills/pptx/scripts/inventory.py, src/doc_generator/infrastructure/image/validator.py
        """
        # Calculate intersection
        x_overlap = max(0, min(self.x2, other.x2) - max(self.x, other.x))
        y_overlap = max(0, min(self.y2, other.y2) - max(self.y, other.y))
        intersection = x_overlap * y_overlap

        # Calculate smaller area
        area1 = self.width * self.height
        area2 = other.width * other.height
        smaller_area = min(area1, area2)

        if smaller_area == 0:
            return False

        overlap_ratio = intersection / smaller_area
        return overlap_ratio > threshold


@dataclass
class ValidationResult:
    """Result of SVG validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]

    @property
    def has_critical_errors(self) -> bool:
        """
        Check if there are critical errors that require regeneration.
        Invoked by: (no references found)
        """
        critical_keywords = ["malformed", "parse error", "invalid", "missing svg"]
        return any(
            any(kw in err.lower() for kw in critical_keywords)
            for err in self.errors
        )


class SVGValidator:
    """
    Validates SVG code for quality and correctness.

    Checks for:
    - Valid XML/SVG structure
    - Text overlap issues
    - Element positioning problems
    - Missing viewBox or dimensions
    """

    # SVG namespace
    SVG_NS = "{http://www.w3.org/2000/svg}"

    # Minimum readable font size
    MIN_FONT_SIZE = 8

    # Maximum overlap threshold for text
    TEXT_OVERLAP_THRESHOLD = 0.3

    # Maximum overlap threshold for shapes
    SHAPE_OVERLAP_THRESHOLD = 0.7

    def validate(self, svg_content: str) -> ValidationResult:
        """
        Validate SVG content.

        Args:
            svg_content: SVG code as string

        Returns:
            ValidationResult with errors, warnings, and suggestions
        Invoked by: .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validate.py, .claude/skills/pptx/ooxml/scripts/validation/base.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/infrastructure/image/validator.py
        """
        errors = []
        warnings = []
        suggestions = []

        # Basic checks
        if not svg_content or not svg_content.strip():
            return ValidationResult(
                is_valid=False,
                errors=["Empty SVG content"],
                warnings=[],
                suggestions=["Generate SVG content"]
            )

        # Check for SVG tag
        if "<svg" not in svg_content.lower():
            return ValidationResult(
                is_valid=False,
                errors=["Missing SVG root element"],
                warnings=[],
                suggestions=["Ensure SVG starts with <svg> tag"]
            )

        # Clean up common issues before parsing
        svg_content = self._clean_svg(svg_content)

        # Parse SVG
        try:
            root = ET.fromstring(svg_content)
        except ET.ParseError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"SVG parse error: {str(e)}"],
                warnings=[],
                suggestions=["Fix XML syntax errors", "Check for unclosed tags"]
            )

        # Validate structure
        structure_errors = self._validate_structure(root)
        errors.extend(structure_errors)

        # Check viewBox and dimensions
        dimension_warnings = self._check_dimensions(root)
        warnings.extend(dimension_warnings)

        # Check for text overlaps
        text_issues = self._check_text_overlaps(root)
        warnings.extend(text_issues)

        # Check for element overlaps
        overlap_issues = self._check_element_overlaps(root)
        warnings.extend(overlap_issues)

        # Check font sizes
        font_issues = self._check_font_sizes(root)
        warnings.extend(font_issues)

        # Generate suggestions
        if warnings:
            suggestions.append("Consider regenerating with adjusted layout")
        if len(warnings) > 3:
            suggestions.append("Multiple layout issues detected - request larger canvas")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def validate_and_fix(self, svg_content: str) -> tuple[str, ValidationResult]:
        """
        Validate SVG and attempt to fix minor issues.

        Args:
            svg_content: SVG code

        Returns:
            Tuple of (fixed_svg, validation_result)
        Invoked by: (no references found)
        """
        # First validation
        result = self.validate(svg_content)

        if not result.is_valid:
            # Try to fix common issues
            fixed_svg = self._attempt_fixes(svg_content)
            result = self.validate(fixed_svg)
            return fixed_svg, result

        return svg_content, result

    def _clean_svg(self, svg_content: str) -> str:
        """
        Clean up common SVG issues before parsing.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        # Remove markdown code blocks if present
        if "```" in svg_content:
            match = re.search(r'<svg[\s\S]*?</svg>', svg_content, re.IGNORECASE)
            if match:
                svg_content = match.group(0)

        # Ensure proper XML declaration handling
        svg_content = svg_content.strip()

        # Remove any text before <svg
        svg_start = svg_content.lower().find("<svg")
        if svg_start > 0:
            svg_content = svg_content[svg_start:]

        # Remove any text after </svg>
        svg_end = svg_content.lower().rfind("</svg>")
        if svg_end > 0:
            svg_content = svg_content[:svg_end + 6]

        return svg_content

    def _validate_structure(self, root: ET.Element) -> list[str]:
        """
        Validate SVG structure.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        errors = []

        # Check root element
        tag_name = root.tag.replace(self.SVG_NS, "").lower()
        if tag_name != "svg":
            errors.append(f"Root element is '{tag_name}', expected 'svg'")

        # Check for at least some content
        if len(root) == 0:
            errors.append("SVG has no child elements")

        return errors

    def _check_dimensions(self, root: ET.Element) -> list[str]:
        """
        Check for proper viewBox and dimensions.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        warnings = []

        # Check viewBox
        viewbox = root.get("viewBox") or root.get("viewbox")
        if not viewbox:
            warnings.append("Missing viewBox attribute - may not scale properly")
        else:
            # Validate viewBox format
            parts = viewbox.split()
            if len(parts) != 4:
                warnings.append(f"Invalid viewBox format: '{viewbox}'")
            else:
                try:
                    _, _, w, h = [float(p) for p in parts]
                    if w <= 0 or h <= 0:
                        warnings.append("viewBox has non-positive dimensions")
                    if w > 2000 or h > 2000:
                        warnings.append("viewBox dimensions very large - may affect rendering")
                except ValueError:
                    warnings.append(f"Invalid viewBox values: '{viewbox}'")

        # Check width/height if no viewBox
        if not viewbox:
            width = root.get("width")
            height = root.get("height")
            if not width or not height:
                warnings.append("Missing both viewBox and width/height attributes")

        return warnings

    def _check_text_overlaps(self, root: ET.Element) -> list[str]:
        """
        Check for overlapping text elements.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        warnings = []
        text_boxes = []

        # Find all text elements
        for elem in root.iter():
            tag = elem.tag.replace(self.SVG_NS, "").lower()
            if tag in ("text", "tspan"):
                bbox = self._estimate_text_bbox(elem)
                if bbox:
                    text_boxes.append((elem.text or "", bbox))

        # Check for overlaps
        for i, (text1, box1) in enumerate(text_boxes):
            for j, (text2, box2) in enumerate(text_boxes[i + 1:], i + 1):
                if box1.overlaps(box2, self.TEXT_OVERLAP_THRESHOLD):
                    warnings.append(
                        f"Text overlap detected: '{text1[:20]}...' and '{text2[:20]}...'"
                    )

        return warnings[:5]  # Limit to first 5 warnings

    def _check_element_overlaps(self, root: ET.Element) -> list[str]:
        """
        Check for significantly overlapping shape elements.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        warnings = []
        shape_boxes = []

        shape_tags = {"rect", "circle", "ellipse", "polygon", "path"}

        for elem in root.iter():
            tag = elem.tag.replace(self.SVG_NS, "").lower()
            if tag in shape_tags:
                bbox = self._estimate_shape_bbox(elem, tag)
                if bbox and bbox.width > 10 and bbox.height > 10:
                    shape_boxes.append((tag, bbox))

        # Check for significant overlaps
        overlap_count = 0
        for i, (tag1, box1) in enumerate(shape_boxes):
            for j, (tag2, box2) in enumerate(shape_boxes[i + 1:], i + 1):
                if box1.overlaps(box2, self.SHAPE_OVERLAP_THRESHOLD):
                    overlap_count += 1

        if overlap_count > 5:
            warnings.append(f"Multiple shape overlaps detected ({overlap_count})")

        return warnings

    def _check_font_sizes(self, root: ET.Element) -> list[str]:
        """
        Check for too-small font sizes.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        warnings = []
        small_fonts = 0

        for elem in root.iter():
            tag = elem.tag.replace(self.SVG_NS, "").lower()
            if tag in ("text", "tspan"):
                font_size = self._get_font_size(elem)
                if font_size and font_size < self.MIN_FONT_SIZE:
                    small_fonts += 1

        if small_fonts > 0:
            warnings.append(f"{small_fonts} text elements with font-size < {self.MIN_FONT_SIZE}px")

        return warnings

    def _estimate_text_bbox(self, elem: ET.Element) -> Optional[BoundingBox]:
        """
        Estimate bounding box for text element.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        try:
            x = float(elem.get("x", 0))
            y = float(elem.get("y", 0))
            text = elem.text or ""

            # Estimate width based on text length and font size
            font_size = self._get_font_size(elem) or 12
            width = len(text) * font_size * 0.6
            height = font_size * 1.2

            return BoundingBox(x, y - height, width, height)
        except (ValueError, TypeError):
            return None

    def _estimate_shape_bbox(self, elem: ET.Element, tag: str) -> Optional[BoundingBox]:
        """
        Estimate bounding box for shape element.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        try:
            if tag == "rect":
                x = float(elem.get("x", 0))
                y = float(elem.get("y", 0))
                width = float(elem.get("width", 0))
                height = float(elem.get("height", 0))
                return BoundingBox(x, y, width, height)

            elif tag == "circle":
                cx = float(elem.get("cx", 0))
                cy = float(elem.get("cy", 0))
                r = float(elem.get("r", 0))
                return BoundingBox(cx - r, cy - r, r * 2, r * 2)

            elif tag == "ellipse":
                cx = float(elem.get("cx", 0))
                cy = float(elem.get("cy", 0))
                rx = float(elem.get("rx", 0))
                ry = float(elem.get("ry", 0))
                return BoundingBox(cx - rx, cy - ry, rx * 2, ry * 2)

        except (ValueError, TypeError):
            pass

        return None

    def _get_font_size(self, elem: ET.Element) -> Optional[float]:
        """
        Extract font size from element.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        # Check font-size attribute
        font_size = elem.get("font-size")
        if font_size:
            match = re.match(r"([\d.]+)", font_size)
            if match:
                return float(match.group(1))

        # Check style attribute
        style = elem.get("style", "")
        match = re.search(r"font-size:\s*([\d.]+)", style)
        if match:
            return float(match.group(1))

        return None

    def _attempt_fixes(self, svg_content: str) -> str:
        """
        Attempt to fix common SVG issues.
        Invoked by: src/doc_generator/infrastructure/image/validator.py
        """
        # Add viewBox if missing
        if "viewBox" not in svg_content and "viewbox" not in svg_content:
            # Try to infer from width/height
            width_match = re.search(r'width="(\d+)', svg_content)
            height_match = re.search(r'height="(\d+)', svg_content)
            if width_match and height_match:
                w, h = width_match.group(1), height_match.group(1)
                svg_content = svg_content.replace(
                    "<svg",
                    f'<svg viewBox="0 0 {w} {h}"',
                    1
                )

        return svg_content


def validate_svg(svg_content: str) -> ValidationResult:
    """
    Convenience function to validate SVG content.

    Args:
        svg_content: SVG code

    Returns:
        ValidationResult
    Invoked by: src/doc_generator/infrastructure/image/validator.py
    """
    validator = SVGValidator()
    return validator.validate(svg_content)


def validate_svg_file(file_path: Path) -> ValidationResult:
    """
    Validate SVG file.

    Args:
        file_path: Path to SVG file

    Returns:
        ValidationResult
    Invoked by: (no references found)
    """
    try:
        svg_content = file_path.read_text(encoding="utf-8")
        return validate_svg(svg_content)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Failed to read SVG file: {e}"],
            warnings=[],
            suggestions=["Check file path and permissions"]
        )
