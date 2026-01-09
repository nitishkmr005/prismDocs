#!/usr/bin/env python3
"""
Generate PDF and PPTX documents from all files in a data subfolder.

This script processes all supported files in a given data subfolder and generates
a single PDF and PPTX output combining content from all files.
"""

import sys
from pathlib import Path
from typing import Optional
import argparse
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doc_generator.application.graph_workflow import run_workflow
from doc_generator.infrastructure.logging_config import setup_logging
from doc_generator.infrastructure.llm_service import LLMService
from doc_generator.domain.content_types import ContentFormat
from doc_generator.utils.content_merger import merge_folder_content


# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.pdf': ContentFormat.PDF,
    '.md': ContentFormat.MARKDOWN,
    '.markdown': ContentFormat.MARKDOWN,
    '.txt': ContentFormat.TEXT,
    '.docx': ContentFormat.DOCX,
    '.pptx': ContentFormat.PPTX,
}


def discover_files(folder_path: Path) -> list[Path]:
    """
    Discover all supported files in the given folder.

    Args:
        folder_path: Path to the folder to scan

    Returns:
        List of file paths with supported extensions
    """
    files = []
    for ext in SUPPORTED_EXTENSIONS.keys():
        files.extend(folder_path.glob(f"*{ext}"))

    # Sort by name for consistent processing order
    return sorted(files)


def process_folder(
    folder_path: Path,
    output_dir: Path,
    llm_service: Optional[LLMService] = None,
    verbose: bool = False,
    skip_image_generation: bool = False
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Process all files in a folder and generate PDF and PPTX outputs.

    Args:
        folder_path: Path to the data subfolder
        output_dir: Directory for output files
        llm_service: Optional LLM service for content enhancement
        verbose: Enable verbose logging
        skip_image_generation: Whether to reuse existing images

    Returns:
        Tuple of (pdf_path, pptx_path) or (None, None) on failure
    """
    logger.info(f"Processing folder: {folder_path}")
    if skip_image_generation:
        logger.info("Image generation will be skipped - reusing existing images")

    # Discover all supported files
    files = discover_files(folder_path)

    if not files:
        logger.error(f"No supported files found in {folder_path}")
        logger.info(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        return None, None

    logger.info(f"Found {len(files)} file(s) to process:")
    for file in files:
        logger.info(f"  - {file.name}")

    # Process each file and collect parsed content
    all_parsed_content = []
    all_metadata = []

    for file_path in files:
        logger.info(f"Processing: {file_path.name}")

        try:
            # Use a temporary output path for intermediate processing
            temp_output = output_dir / f"temp_{file_path.stem}.pdf"

            # Run workflow to parse and transform the content
            result = run_workflow(
                input_path=str(file_path),
                output_format="pdf",
                output_path=str(temp_output),
                llm_service=llm_service
            )

            # Check if processing was successful (no errors and has output_path)
            if not result.get("errors") and result.get("output_path"):
                all_parsed_content.append({
                    "filename": file_path.name,
                    "raw_content": result.get("raw_content", ""),
                    "structured_content": result.get("structured_content", ""),
                    "metadata": result.get("metadata", {})
                })
                all_metadata.append(result.get("metadata", {}))
                logger.success(f"Successfully processed: {file_path.name}")

                # Clean up temporary file
                if temp_output.exists():
                    temp_output.unlink()
            else:
                errors = result.get("errors", ["Unknown error"])
                logger.warning(f"Failed to process {file_path.name}: {errors}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            continue

    if not all_parsed_content:
        logger.error("No files were successfully processed")
        return None, None

    # Merge all content
    logger.info("Merging content from all files...")
    merged_content = merge_folder_content(
        all_parsed_content,
        folder_name=folder_path.name,
        llm_service=llm_service
    )

    # Generate output file names based on folder name
    topic_name = folder_path.name
    pdf_output = output_dir / f"{topic_name}.pdf"
    pptx_output = output_dir / f"{topic_name}.pptx"

    # Generate PDF
    logger.info(f"Generating PDF: {pdf_output}")
    
    # Add image reuse flag to metadata
    pdf_metadata = merged_content["metadata"].copy()
    if skip_image_generation:
        pdf_metadata["skip_image_generation"] = True
    
    pdf_result = run_workflow(
        input_path=merged_content["temp_file"],
        output_format="pdf",
        output_path=str(pdf_output),
        llm_service=llm_service,
        metadata=pdf_metadata
    )

    pdf_path = None
    if not pdf_result.get("errors") and pdf_result.get("output_path"):
        pdf_path = Path(pdf_result["output_path"])
        logger.success(f"PDF generated: {pdf_path}")
    else:
        errors = pdf_result.get("errors", ["Unknown error"])
        logger.error(f"PDF generation failed: {errors}")

    # Generate PPTX
    logger.info(f"Generating PPTX: {pptx_output}")
    
    # Add image reuse flag to metadata
    pptx_metadata = merged_content["metadata"].copy()
    if skip_image_generation:
        pptx_metadata["skip_image_generation"] = True
    
    pptx_result = run_workflow(
        input_path=merged_content["temp_file"],
        output_format="pptx",
        output_path=str(pptx_output),
        llm_service=llm_service,
        metadata=pptx_metadata
    )

    pptx_path = None
    if not pptx_result.get("errors") and pptx_result.get("output_path"):
        pptx_path = Path(pptx_result["output_path"])
        logger.success(f"PPTX generated: {pptx_path}")
    else:
        errors = pptx_result.get("errors", ["Unknown error"])
        logger.error(f"PPTX generation failed: {errors}")

    # Clean up temporary merged content file
    temp_file = Path(merged_content["temp_file"])
    if temp_file.exists():
        temp_file.unlink()

    return pdf_path, pptx_path


def main():
    """Main entry point for the folder-based document generator."""
    parser = argparse.ArgumentParser(
        description="Generate PDF and PPTX from all files in a data subfolder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_from_folder.py data/llm-architectures
  python scripts/generate_from_folder.py data/my-topic --api-key YOUR_KEY
  python scripts/generate_from_folder.py data/my-topic --verbose
        """
    )

    parser.add_argument(
        "folder",
        type=str,
        help="Path to data subfolder (e.g., data/llm-architectures)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="src/output",
        help="Output directory (default: src/output)"
    )

    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key for LLM-enhanced content (optional)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (optional)"
    )
    
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation and reuse existing images"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Validate folder path
    folder_path = Path(args.folder)
    if not folder_path.exists():
        logger.error(f"Folder not found: {folder_path}")
        sys.exit(1)

    if not folder_path.is_dir():
        logger.error(f"Path is not a directory: {folder_path}")
        sys.exit(1)

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize LLM service if API key provided
    llm_service = None
    if args.api_key:
        try:
            llm_service = LLMService(api_key=args.api_key)
            logger.info("LLM service initialized for content enhancement")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM service: {e}")
            logger.info("Continuing without LLM enhancement")

    # Process the folder
    try:
        pdf_path, pptx_path = process_folder(
            folder_path=folder_path,
            output_dir=output_dir,
            llm_service=llm_service,
            verbose=args.verbose,
            skip_image_generation=args.skip_images
        )

        # Report results
        if pdf_path or pptx_path:
            logger.success("\n" + "="*60)
            logger.success("GENERATION COMPLETE")
            logger.success("="*60)
            if pdf_path:
                logger.success(f"PDF:  {pdf_path}")
            if pptx_path:
                logger.success(f"PPTX: {pptx_path}")
            logger.success("="*60)
            sys.exit(0)
        else:
            logger.error("Failed to generate documents")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            logger.exception("Stack trace:")
        sys.exit(1)


if __name__ == "__main__":
    main()
