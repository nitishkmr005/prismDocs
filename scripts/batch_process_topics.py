#!/usr/bin/env python3
"""
Batch process all topic folders in the data directory.

This script discovers all subdirectories in src/data/ and processes each one
as a separate topic, generating combined PDF and PPTX for each folder.

Usage:
    python scripts/batch_process_topics.py
    python scripts/batch_process_topics.py --skip-images
    python scripts/batch_process_topics.py --data-dir custom/path
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doc_generator.infrastructure.llm_service import LLMService
from doc_generator.infrastructure.logging_config import setup_logging

# Import the folder processor
from generate_from_folder import process_folder


def discover_topic_folders(data_dir: Path) -> list[Path]:
    """
    Discover all subdirectories in the data directory.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        List of subdirectory paths (topic folders)
    Invoked by: scripts/batch_process_topics.py
    """
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return []
    
    # Find all subdirectories (excluding hidden folders)
    folders = [
        folder for folder in data_dir.iterdir()
        if folder.is_dir() and not folder.name.startswith('.')
    ]
    
    return sorted(folders)


def batch_process_topics(
    data_dir: Path = Path("src/data"),
    output_dir: Path = Path("src/output"),
    skip_images: bool = False,
    api_key: str = None,
    verbose: bool = False
) -> dict:
    """
    Process all topic folders in the data directory.
    
    Args:
        data_dir: Path to data directory containing topic subfolders
        output_dir: Path to output directory
        skip_images: Whether to skip image generation (reuse existing)
        api_key: Optional API key for LLM service
        verbose: Enable verbose logging
        
    Returns:
        Dict with processing results
    Invoked by: scripts/batch_process_topics.py
    """
    logger.info("=" * 80)
    logger.info("BATCH PROCESSING ALL TOPICS")
    logger.info("=" * 80)
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output directory: {output_dir}")
    if skip_images:
        logger.info("Mode: Reusing existing images (skip generation)")
    else:
        logger.info("Mode: Full processing with image generation")
    logger.info("=" * 80)
    
    # Discover topic folders
    topic_folders = discover_topic_folders(data_dir)
    
    if not topic_folders:
        logger.error(f"No topic folders found in {data_dir}")
        return {"success": False, "processed": 0, "failed": 0}
    
    logger.info(f"Found {len(topic_folders)} topic folder(s):")
    for folder in topic_folders:
        logger.info(f"  - {folder.name}")
    logger.info("")
    
    # Initialize LLM service if API key provided
    llm_service = None
    if api_key:
        try:
            llm_service = LLMService(api_key=api_key)
            logger.info("LLM service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM service: {e}")
    
    # Process each folder
    results = {
        "success": True,
        "processed": 0,
        "failed": 0,
        "topics": {}
    }
    
    for idx, folder in enumerate(topic_folders, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"PROCESSING TOPIC {idx}/{len(topic_folders)}: {folder.name}")
        logger.info("=" * 80)
        
        try:
            pdf_path, pptx_path = process_folder(
                folder_path=folder,
                output_dir=output_dir,
                llm_service=llm_service,
                verbose=verbose,
                skip_image_generation=skip_images
            )
            
            if pdf_path or pptx_path:
                results["processed"] += 1
                results["topics"][folder.name] = {
                    "status": "success",
                    "pdf": str(pdf_path) if pdf_path else None,
                    "pptx": str(pptx_path) if pptx_path else None
                }
                logger.success(f"✅ Successfully processed: {folder.name}")
            else:
                results["failed"] += 1
                results["topics"][folder.name] = {
                    "status": "failed",
                    "pdf": None,
                    "pptx": None
                }
                logger.error(f"❌ Failed to process: {folder.name}")
        
        except Exception as e:
            results["failed"] += 1
            results["topics"][folder.name] = {
                "status": "error",
                "error": str(e),
                "pdf": None,
                "pptx": None
            }
            logger.error(f"❌ Error processing {folder.name}: {e}")
            if verbose:
                logger.exception("Stack trace:")
    
    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total topics: {len(topic_folders)}")
    logger.info(f"Successfully processed: {results['processed']}")
    logger.info(f"Failed: {results['failed']}")
    logger.info("")
    
    if results["processed"] > 0:
        logger.info("Generated documents:")
        for topic_name, topic_result in results["topics"].items():
            if topic_result["status"] == "success":
                logger.info(f"\n{topic_name}:")
                if topic_result["pdf"]:
                    logger.info(f"  PDF:  {topic_result['pdf']}")
                if topic_result["pptx"]:
                    logger.info(f"  PPTX: {topic_result['pptx']}")
    
    if results["failed"] > 0:
        logger.warning(f"\n{results['failed']} topic(s) failed - check logs for details")
    
    logger.info("=" * 80)
    
    results["success"] = results["failed"] == 0
    return results


def main():
    """
    Main entry point for batch topic processor.
    Invoked by: .claude/skills/pdf/scripts/check_bounding_boxes_test.py, .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validate.py, .claude/skills/pptx/scripts/inventory.py, .claude/skills/pptx/scripts/rearrange.py, .claude/skills/pptx/scripts/replace.py, .claude/skills/pptx/scripts/thumbnail.py, .claude/skills/skill-creator/scripts/init_skill.py, .claude/skills/skill-creator/scripts/package_skill.py, scripts/batch_process_topics.py, scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/run_generator.py
    """
    parser = argparse.ArgumentParser(
        description="Batch process all topic folders in data directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all topics with full generation
  python scripts/batch_process_topics.py

  # Reuse existing images (faster)
  python scripts/batch_process_topics.py --skip-images

  # Custom data directory
  python scripts/batch_process_topics.py --data-dir path/to/data

  # With API key for LLM enhancement
  python scripts/batch_process_topics.py --api-key YOUR_KEY --skip-images
        """
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="src/data",
        help="Data directory containing topic subfolders (default: src/data)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="src/output",
        help="Output directory (default: src/output)"
    )
    
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image generation and reuse existing images (much faster)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for LLM service (optional)"
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
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose, log_file=args.log_file)
    
    # Validate paths
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run batch processing
    try:
        results = batch_process_topics(
            data_dir=data_dir,
            output_dir=output_dir,
            skip_images=args.skip_images,
            api_key=args.api_key,
            verbose=args.verbose
        )
        
        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            logger.exception("Stack trace:")
        sys.exit(1)


if __name__ == "__main__":
    main()
