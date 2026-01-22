"""
LangGraph workflow nodes.

Nodes for document generation workflow and unified content workflow.
"""

# Original document generation nodes
from .detect_format import detect_format_node
from .describe_images import describe_images_node
from .enhance_content import enhance_content_node
from .generate_images import generate_images_node
from .generate_output import generate_output_node
from .parse_content import parse_document_content_node
from .persist_image_manifest import persist_image_manifest_node
from .transform_content import transform_content_node
from .validate_output import validate_output_node

# New unified workflow nodes
from .extract_sources import ingest_sources_node, route_by_output_type
from .summarize_sources import summarize_sources_node
from .podcast_nodes import generate_podcast_script_node, synthesize_podcast_audio_node
from .mindmap_nodes import generate_mindmap_node
from .image_nodes import generate_image_node, edit_image_node

__all__ = [
    # Document nodes
    "detect_format_node",
    "parse_document_content_node",
    "transform_content_node",
    "enhance_content_node",
    "generate_images_node",
    "describe_images_node",
    "persist_image_manifest_node",
    "generate_output_node",
    "validate_output_node",
    # Unified workflow nodes
    "ingest_sources_node",
    "summarize_sources_node",
    "route_by_output_type",
    "generate_podcast_script_node",
    "synthesize_podcast_audio_node",
    "generate_mindmap_node",
    "generate_image_node",
    "edit_image_node",
]
