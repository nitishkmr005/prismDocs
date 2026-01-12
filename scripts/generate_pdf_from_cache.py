#!/usr/bin/env python3
"""
Generate PDF from cached content and existing images.

This script allows you to regenerate PDFs without running LLM processing
or image generation, using cached structured content and existing images.
"""

import argparse
from pathlib import Path

from loguru import logger

from doc_generator.application.graph_workflow import run_workflow
from doc_generator.utils.content_cache import load_existing_images, load_structured_content


def generate_pdf_from_cache(
    input_path: str,
    output_path: str = "",
    use_cached_content: bool = True,
    use_existing_images: bool = True
) -> Path:
    """
    Generate PDF using cached content and existing images.
    
    Args:
        input_path: Path to original input file (for cache lookup)
        output_path: Optional custom output path
        use_cached_content: Whether to load cached structured content
        use_existing_images: Whether to load existing images
        
    Returns:
        Path to generated PDF
    Invoked by: scripts/generate_pdf_from_cache.py
    """
    logger.info("=" * 80)
    logger.info(f"Generating PDF from cache: {input_path}")
    logger.info("=" * 80)
    
    # Metadata to control workflow behavior
    metadata = {
        "skip_image_generation": use_existing_images,
        "use_cache": use_cached_content
    }
    
    # Run workflow with skip flags
    result = run_workflow(
        input_path=input_path,
        output_format="pdf",
        output_path=output_path,
        metadata=metadata
    )
    
    if result.get("errors"):
        logger.error(f"PDF generation failed: {result['errors']}")
        return None
    
    output = result.get("output_path")
    logger.success(f"PDF generated: {output}")
    return output


def main():
    """
    CLI for generating PDFs from cache.
    Invoked by: .claude/skills/pdf/scripts/check_bounding_boxes_test.py, .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validate.py, .claude/skills/pptx/scripts/inventory.py, .claude/skills/pptx/scripts/rearrange.py, .claude/skills/pptx/scripts/replace.py, .claude/skills/pptx/scripts/thumbnail.py, .claude/skills/skill-creator/scripts/init_skill.py, .claude/skills/skill-creator/scripts/package_skill.py, scripts/batch_process_topics.py, scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/run_generator.py
    """
    parser = argparse.ArgumentParser(
        description="Generate PDF from cached content and existing images"
    )
    parser.add_argument(
        "input_path",
        help="Path to original input file (for cache lookup)"
    )
    parser.add_argument(
        "-o", "--output",
        default="",
        help="Output PDF path (default: auto-generated)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached content (reprocess with LLM)"
    )
    parser.add_argument(
        "--regenerate-images",
        action="store_true",
        help="Regenerate images instead of reusing existing ones"
    )
    
    args = parser.parse_args()
    
    # Generate PDF
    output = generate_pdf_from_cache(
        input_path=args.input_path,
        output_path=args.output,
        use_cached_content=not args.no_cache,
        use_existing_images=not args.regenerate_images
    )
    
    if output:
        logger.info(f"Done! PDF saved to: {output}")
    else:
        logger.error("PDF generation failed")
        exit(1)


if __name__ == "__main__":
    main()
