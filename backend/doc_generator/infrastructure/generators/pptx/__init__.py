"""PPTX generator module."""

from .generator import PPTXGenerator
from .utils import (
    create_presentation,
    add_title_slide,
    add_content_slide,
)

__all__ = [
    "PPTXGenerator",
    "create_presentation",
    "add_title_slide",
    "add_content_slide",
]
