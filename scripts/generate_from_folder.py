#!/usr/bin/env python3
"""
Generate PDF and PPTX documents from all files in a data subfolder.

This script processes all supported files in a given data subfolder and generates
a single PDF and PPTX output combining content from all files.
"""

import sys
import time
from pathlib import Path
from typing import Optional
import argparse
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# Progress Logging Utilities
# ============================================================================

class ProgressLogger:
    """Helper for colorful progress logging with emojis."""

    STAGES = {
        "discover": ("📂", "Discovering files"),
        "parse": ("📄", "Parsing files"),
        "merge": ("🔀", "Merging content"),
        "transform": ("🤖", "LLM transformation"),
        "images": ("🎨", "Generating images"),
        "pdf": ("📕", "Creating PDF"),
        "pptx": ("📊", "Creating PPTX"),
        "complete": ("✅", "Complete"),
    }

    def __init__(self, topic_name: str, total_steps: int = 5):
        """
        Invoked by: (no references found)
        """
        self.topic_name = topic_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.step_start_time = time.time()

    def _elapsed(self) -> str:
        """
        Get elapsed time string.
        Invoked by: scripts/generate_from_folder.py
        """
        elapsed = time.time() - self.start_time
        return f"{elapsed:.1f}s"

    def _step_elapsed(self) -> str:
        """
        Get step elapsed time string.
        Invoked by: scripts/generate_from_folder.py
        """
        elapsed = time.time() - self.step_start_time
        return f"{elapsed:.1f}s"

    def header(self):
        """
        Print workflow header.
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/infrastructure/api/services/generation.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/pdf_utils.py
        """
        print("\n" + "=" * 70)
        print(f"🚀 DOCUMENT GENERATOR - Processing: {self.topic_name}")
        print("=" * 70)
        print(f"📋 Workflow: Parse → Merge → Transform → Images → PDF → PPTX")
        print("-" * 70)

    def stage(self, stage_key: str, message: str = ""):
        """
        Start a new stage.
        Invoked by: scripts/generate_from_folder.py
        """
        self.current_step += 1
        self.step_start_time = time.time()
        emoji, stage_name = self.STAGES.get(stage_key, ("▶️", stage_key))
        progress = f"[{self.current_step}/{self.total_steps}]"
        print(f"\n{emoji} {progress} {stage_name}")
        if message:
            print(f"   └── {message}")

    def substep(self, message: str, status: str = "info"):
        """
        Log a substep within a stage.
        Invoked by: scripts/generate_from_folder.py
        """
        icons = {
            "info": "   ├──",
            "success": "   ├── ✓",
            "warning": "   ├── ⚠️",
            "error": "   ├── ❌",
            "progress": "   ├── ⏳",
        }
        icon = icons.get(status, "   ├──")
        print(f"{icon} {message}")

    def substep_done(self, message: str):
        """
        Log final substep (uses └── instead of ├──).
        Invoked by: (no references found)
        """
        print(f"   └── ✓ {message}")

    def stage_complete(self, message: str = ""):
        """
        Mark stage as complete.
        Invoked by: scripts/generate_from_folder.py
        """
        elapsed = self._step_elapsed()
        if message:
            print(f"   └── ✅ {message} ({elapsed})")
        else:
            print(f"   └── ✅ Done ({elapsed})")

    def summary(self, pdf_path: Optional[Path], pptx_path: Optional[Path]):
        """
        Print final summary.
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/utils/content_merger.py
        """
        total_time = time.time() - self.start_time
        print("\n" + "=" * 70)
        print("✨ GENERATION COMPLETE")
        print("=" * 70)
        print(f"📁 Topic: {self.topic_name}")
        print(f"⏱️  Total time: {total_time:.1f}s")
        print("-" * 70)
        if pdf_path:
            size_mb = pdf_path.stat().st_size / (1024 * 1024)
            print(f"📕 PDF:  {pdf_path} ({size_mb:.1f} MB)")
        if pptx_path:
            size_mb = pptx_path.stat().st_size / (1024 * 1024)
            print(f"📊 PPTX: {pptx_path} ({size_mb:.1f} MB)")
        print("=" * 70 + "\n")

    def error(self, message: str):
        """
        Print error message.
        Invoked by: .claude/skills/pptx/ooxml/scripts/validation/base.py, .claude/skills/pptx/ooxml/scripts/validation/docx.py, .claude/skills/pptx/ooxml/scripts/validation/pptx.py, .claude/skills/pptx/scripts/replace.py, scripts/batch_process_topics.py, scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/quick_pdf_with_images.py, scripts/run_generator.py, src/doc_generator/application/graph_workflow.py, src/doc_generator/application/nodes/detect_format.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/nodes/parse_content.py, src/doc_generator/application/nodes/transform_content.py, src/doc_generator/application/nodes/validate_output.py, src/doc_generator/application/parsers/markdown_parser.py, src/doc_generator/application/parsers/unified_parser.py, src/doc_generator/application/parsers/web_parser.py, src/doc_generator/application/workflow/graph.py, src/doc_generator/application/workflow/nodes/detect_format.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/parse_content.py, src/doc_generator/application/workflow/nodes/transform_content.py, src/doc_generator/application/workflow/nodes/validate_output.py, src/doc_generator/infrastructure/api/services/generation.py, src/doc_generator/infrastructure/generators/pdf/utils.py, src/doc_generator/infrastructure/generators/pptx/utils.py, src/doc_generator/infrastructure/image/claude_svg.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/image/svg.py, src/doc_generator/infrastructure/llm/content_generator.py, src/doc_generator/infrastructure/llm/service.py, src/doc_generator/infrastructure/logging/config.py, src/doc_generator/infrastructure/logging_config.py, src/doc_generator/infrastructure/parsers/docling.py, src/doc_generator/infrastructure/parsers/file_system.py, src/doc_generator/infrastructure/parsers/markitdown.py, src/doc_generator/infrastructure/pdf_utils.py, src/doc_generator/infrastructure/pptx_utils.py, src/doc_generator/infrastructure/settings.py, tests/api/test_response_models.py
        """
        print(f"\n❌ ERROR: {message}")
        print(f"⏱️  Failed after {self._elapsed()}\n")

from doc_generator.application.graph_workflow import run_workflow
from doc_generator.application.parsers import get_parser
from doc_generator.infrastructure.logging_config import setup_logging
from doc_generator.infrastructure.llm_service import LLMService
from doc_generator.domain.content_types import ContentFormat
from doc_generator.utils.content_merger import merge_folder_content
from doc_generator.application.generators import get_generator
from doc_generator.infrastructure.settings import get_settings


# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.pdf': ContentFormat.PDF,
    '.md': ContentFormat.MARKDOWN,
    '.markdown': ContentFormat.MARKDOWN,
    '.txt': ContentFormat.TEXT,
    '.docx': ContentFormat.DOCX,
    '.pptx': ContentFormat.PPTX,
}


def parse_file_only(file_path: Path) -> dict | None:
    """
    Parse a file without running full workflow (no LLM, no output generation).

    This is much faster than run_workflow as it only extracts raw content.

    Args:
        file_path: Path to file to parse

    Returns:
        Dict with filename, raw_content, metadata or None on failure
    Invoked by: scripts/generate_from_folder.py
    """
    try:
        # Detect format from extension
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported format: {suffix}")
            return None

        input_format = suffix.lstrip('.')  # e.g., ".pdf" -> "pdf"

        # Get appropriate parser
        parser = get_parser(input_format)

        # Parse content (no LLM transformation)
        raw_content, metadata = parser.parse(str(file_path))

        return {
            "filename": file_path.name,
            "raw_content": raw_content,
            "structured_content": "",  # Not transformed yet
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Failed to parse {file_path.name}: {e}")
        return None


def discover_files(folder_path: Path) -> list[Path]:
    """
    Discover all supported files in the given folder.

    Args:
        folder_path: Path to the folder to scan

    Returns:
        List of file paths with supported extensions
    Invoked by: scripts/generate_from_folder.py
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
    Invoked by: scripts/batch_process_topics.py, scripts/generate_from_folder.py
    """
    topic_name = folder_path.name
    progress = ProgressLogger(topic_name, total_steps=5)
    progress.header()

    if skip_image_generation:
        print("⚡ Fast mode: Reusing existing images")

    # =========================================================================
    # STAGE 1: Discover files
    # =========================================================================
    progress.stage("discover", f"Scanning {folder_path}")
    files = discover_files(folder_path)

    if not files:
        progress.error(f"No supported files found in {folder_path}")
        print(f"   Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        return None, None

    for f in files:
        progress.substep(f"{f.name}", "info")
    progress.stage_complete(f"Found {len(files)} file(s)")

    # =========================================================================
    # STAGE 2: Parse files (fast - no LLM)
    # =========================================================================
    progress.stage("parse", f"Extracting content from {len(files)} file(s)")
    all_parsed_content = []
    total_chars = 0

    for i, file_path in enumerate(files, 1):
        progress.substep(f"[{i}/{len(files)}] {file_path.name}", "progress")
        result = parse_file_only(file_path)
        if result:
            all_parsed_content.append(result)
            chars = len(result['raw_content'])
            total_chars += chars

    if not all_parsed_content:
        progress.error("No files were successfully parsed")
        return None, None

    progress.stage_complete(f"Parsed {len(all_parsed_content)} files ({total_chars:,} chars)")

    # =========================================================================
    # STAGE 3: Merge & Transform with LLM
    # =========================================================================
    progress.stage("merge", "Combining content & LLM transformation")
    progress.substep("Sending to LLM for blog-style transformation...", "progress")

    merged_content = merge_folder_content(
        all_parsed_content,
        folder_name=topic_name,
        llm_service=llm_service
    )

    output_chars = len(Path(merged_content["temp_file"]).read_text())
    progress.stage_complete(f"Generated {output_chars:,} chars markdown")

    # Setup output paths
    topic_output_dir = output_dir / topic_name
    topic_output_dir.mkdir(parents=True, exist_ok=True)
    pdf_output = topic_output_dir / f"{topic_name}.pdf"
    pptx_output = topic_output_dir / f"{topic_name}.pptx"

    # =========================================================================
    # STAGE 4: Generate PDF (includes images)
    # =========================================================================
    img_status = "reusing existing" if skip_image_generation else "generating new"
    progress.stage("pdf", f"Creating PDF ({img_status} images)")

    pdf_metadata = merged_content["metadata"].copy()
    if skip_image_generation:
        pdf_metadata["skip_image_generation"] = True

    progress.substep("Running PDF workflow (transform → images → render)...", "progress")

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
        size_mb = pdf_path.stat().st_size / (1024 * 1024)
        progress.stage_complete(f"PDF ready: {pdf_path.name} ({size_mb:.1f} MB)")
    else:
        errors = pdf_result.get("errors", ["Unknown error"])
        progress.substep(f"PDF failed: {errors}", "error")

    # =========================================================================
    # STAGE 5: Generate PPTX (reuses structured content)
    # =========================================================================
    progress.stage("pptx", "Creating PPTX (reusing PDF content)")

    pptx_path = None
    if pdf_result and pdf_result.get("structured_content"):
        progress.substep("Reusing structured content from PDF...", "progress")
        try:
            pptx_generator = get_generator("pptx")
            pptx_output_path = pptx_generator.generate(
                content=pdf_result["structured_content"],
                metadata=pdf_result.get("metadata", merged_content["metadata"]),
                output_dir=topic_output_dir
            )
            pptx_path = Path(pptx_output_path)
            size_mb = pptx_path.stat().st_size / (1024 * 1024)
            progress.stage_complete(f"PPTX ready: {pptx_path.name} ({size_mb:.1f} MB)")
        except Exception as e:
            progress.substep(f"PPTX failed: {e}", "error")
    else:
        progress.substep("No cached content, running full workflow...", "warning")
        pptx_metadata = merged_content["metadata"].copy()
        pptx_metadata["skip_image_generation"] = True

        pptx_result = run_workflow(
            input_path=merged_content["temp_file"],
            output_format="pptx",
            output_path=str(pptx_output),
            llm_service=llm_service,
            metadata=pptx_metadata
        )

        if not pptx_result.get("errors") and pptx_result.get("output_path"):
            pptx_path = Path(pptx_result["output_path"])
            size_mb = pptx_path.stat().st_size / (1024 * 1024)
            progress.stage_complete(f"PPTX ready: {pptx_path.name} ({size_mb:.1f} MB)")
        else:
            errors = pptx_result.get("errors", ["Unknown error"])
            progress.substep(f"PPTX failed: {errors}", "error")

    # =========================================================================
    # Summary
    # =========================================================================
    progress.summary(pdf_path, pptx_path)

    return pdf_path, pptx_path


def main():
    """
    Main entry point for the folder-based document generator.
    Invoked by: .claude/skills/pdf/scripts/check_bounding_boxes_test.py, .claude/skills/pptx/ooxml/scripts/pack.py, .claude/skills/pptx/ooxml/scripts/validate.py, .claude/skills/pptx/scripts/inventory.py, .claude/skills/pptx/scripts/rearrange.py, .claude/skills/pptx/scripts/replace.py, .claude/skills/pptx/scripts/thumbnail.py, .claude/skills/skill-creator/scripts/init_skill.py, .claude/skills/skill-creator/scripts/package_skill.py, scripts/batch_process_topics.py, scripts/generate_from_folder.py, scripts/generate_pdf_from_cache.py, scripts/run_generator.py
    """
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

        # Exit with appropriate code
        if pdf_path or pptx_path:
            sys.exit(0)
        else:
            print("\n❌ Failed to generate documents")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
