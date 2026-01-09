#!/usr/bin/env python3
"""
Quick PDF generation using existing images.

Usage:
    python scripts/quick_pdf_with_images.py <input_file>

This will generate a PDF using the existing images in src/output/images/
without regenerating them.
"""

import sys
from pathlib import Path

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doc_generator.application.graph_workflow import run_workflow


def quick_pdf_with_existing_images(input_path: str) -> Path:
    """
    Generate PDF using existing images, skipping image generation.
    
    Args:
        input_path: Path to input file
        
    Returns:
        Path to generated PDF
    """
    logger.info("=" * 80)
    logger.info(f"Quick PDF generation with existing images")
    logger.info(f"Input: {input_path}")
    logger.info("=" * 80)
    
    # Run workflow with skip_image_generation flag
    result = run_workflow(
        input_path=input_path,
        output_format="pdf",
        metadata={"skip_image_generation": True}
    )
    
    if result.get("errors"):
        logger.error(f"PDF generation failed with errors:")
        for error in result.get("errors", []):
            logger.error(f"  - {error}")
        return None
    
    output = result.get("output_path")
    logger.success(f"\n✅ PDF generated successfully: {output}")
    return output


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/quick_pdf_with_images.py <input_file>")
        print("\nExample:")
        print("  python scripts/quick_pdf_with_images.py src/data/llm-architectures/Transformers-Internals_slides.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    output = quick_pdf_with_existing_images(input_file)
    
    if not output:
        sys.exit(1)
