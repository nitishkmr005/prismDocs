"""
Logging configuration for document generator.

Configures loguru for structured logging with custom formatting,
visual separators, and stats tracking.
"""

import logging
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


# ANSI color codes for terminal
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


@dataclass
class ProcessStats:
    """Track statistics for a generation process."""
    start_time: float = field(default_factory=time.time)
    llm_calls: int = 0
    image_calls: int = 0
    files_processed: int = 0
    errors: int = 0
    warnings: int = 0
    
    def elapsed(self) -> float:
        """
        Get elapsed time in seconds.
        Invoked by: scripts/generate_from_folder.py, src/doc_generator/infrastructure/image/gemini.py, src/doc_generator/infrastructure/logging/config.py, src/doc_generator/infrastructure/logging_config.py
        """
        return time.time() - self.start_time
    
    def format_elapsed(self) -> str:
        """
        Format elapsed time as human-readable string.
        Invoked by: src/doc_generator/infrastructure/logging/config.py, src/doc_generator/infrastructure/logging_config.py
        """
        elapsed = self.elapsed()
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        return f"{minutes}m {seconds:.1f}s"


# Global stats tracker
_current_stats: Optional[ProcessStats] = None


def get_current_stats() -> Optional[ProcessStats]:
    """
    Get current process stats.
    Invoked by: (no references found)
    """
    return _current_stats


def setup_logging(verbose: bool = False, log_file: str | None = None) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable debug logging if True
        log_file: Path to log file (optional)
    Invoked by: scripts/batch_process_topics.py, scripts/generate_from_folder.py, scripts/run_generator.py, src/doc_generator/infrastructure/api/main.py
    """
    # Remove default logger
    logger.remove()

    # Determine log level
    level = "DEBUG" if verbose else "INFO"

    # Custom format with better visual hierarchy
    # - Compact module names for cleaner output
    # - Different colors for different components
    console_format = (
        "<dim>{time:HH:mm:ss}</dim> │ "
        "<level>{level: <8}</level> │ "
        "<cyan>{name: <25}</cyan> │ "
        "<level>{message}</level>"
    )

    # Console logging with color
    logger.add(
        sys.stderr,
        level=level,
        format=console_format,
        colorize=True,
    )

    # File logging if requested
    if log_file:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        logger.add(
            log_file,
            level=level,
            format=file_format,
            rotation="10 MB",
            retention="7 days",
        )
        logger.info(f"Logging to file: {log_file}")

    # Suppress verbose logging from third-party libraries
    for lib in ["docling", "PIL", "pdfminer", "httpx", "httpcore", "urllib3", "google"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    logger.info(f"Logging configured (level={level})")


def log_separator(title: str = "", char: str = "─", width: int = 60) -> None:
    """
    Print a visual separator line to the log.
    Invoked by: src/doc_generator/infrastructure/api/services/generation.py
    """
    if title:
        padding = (width - len(title) - 2) // 2
        line = f"{char * padding} {title} {char * padding}"
        if len(line) < width:
            line += char
    else:
        line = char * width
    logger.opt(colors=True).info(f"<dim>{line}</dim>")


def log_phase(phase_num: int, total_phases: int, title: str) -> None:
    """
    Log the start of a new phase with visual formatting.
    Invoked by: src/doc_generator/infrastructure/api/services/generation.py
    """
    logger.opt(colors=True).info("")
    logger.opt(colors=True).info(f"<bold><blue>▶ Phase {phase_num}/{total_phases}: {title}</blue></bold>")
    logger.opt(colors=True).info(f"<dim>{'─' * 50}</dim>")


def log_success(message: str) -> None:
    """
    Log a success message with green checkmark.
    Invoked by: src/doc_generator/infrastructure/api/services/generation.py
    """
    logger.opt(colors=True).success(f"<green>✓</green> {message}")


def log_warning(message: str) -> None:
    """
    Log a warning message with yellow icon.
    Invoked by: (no references found)
    """
    logger.opt(colors=True).warning(f"<yellow>⚠</yellow> {message}")


def log_error(message: str) -> None:
    """
    Log an error message with red X.
    Invoked by: (no references found)
    """
    logger.opt(colors=True).error(f"<red>✗</red> {message}")


def log_stats(stats: dict, title: str = "Statistics") -> None:
    """
    Log statistics in a formatted box.
    Invoked by: src/doc_generator/infrastructure/api/services/generation.py, src/doc_generator/infrastructure/logging/config.py, src/doc_generator/infrastructure/logging_config.py
    """
    logger.opt(colors=True).info("")
    logger.opt(colors=True).info(f"<bold><magenta>╔{'═' * 40}╗</magenta></bold>")
    logger.opt(colors=True).info(f"<bold><magenta>║  {title: <36}  ║</magenta></bold>")
    logger.opt(colors=True).info(f"<bold><magenta>╠{'═' * 40}╣</magenta></bold>")
    
    for key, value in stats.items():
        key_str = f"  {key}:"
        value_str = str(value)
        padding = 36 - len(key_str) - len(value_str)
        logger.opt(colors=True).info(f"<magenta>║</magenta>{key_str}{' ' * padding}{value_str}<magenta>  ║</magenta>")
    
    logger.opt(colors=True).info(f"<bold><magenta>╚{'═' * 40}╝</magenta></bold>")
    logger.opt(colors=True).info("")


@contextmanager
def log_process(name: str):
    """
    Context manager to track and log a process with timing.
    Invoked by: (no references found)
    """
    global _current_stats
    stats = ProcessStats()
    _current_stats = stats
    
    logger.opt(colors=True).info("")
    logger.opt(colors=True).info(f"<bold><cyan>{'═' * 60}</cyan></bold>")
    logger.opt(colors=True).info(f"<bold><cyan>  🚀 Starting: {name}</cyan></bold>")
    logger.opt(colors=True).info(f"<bold><cyan>{'═' * 60}</cyan></bold>")
    
    try:
        yield stats
        # Log completion stats
        completion_stats = {
            "Duration": stats.format_elapsed(),
            "LLM Calls": stats.llm_calls,
            "Images Generated": stats.image_calls,
            "Files Processed": stats.files_processed,
            "Errors": stats.errors,
        }
        log_stats(completion_stats, f"✅ {name} Complete")
    except Exception as e:
        stats.errors += 1
        logger.opt(colors=True).error(f"<red>{'═' * 60}</red>")
        logger.opt(colors=True).error(f"<red>  ❌ {name} Failed: {str(e)}</red>")
        logger.opt(colors=True).error(f"<red>{'═' * 60}</red>")
        raise
    finally:
        _current_stats = None


def log_table(headers: list[str], rows: list[list[str]], title: str = "") -> None:
    """
    Log data in a formatted table.
    Invoked by: (no references found)
    """
    if not rows:
        return
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Build separator
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    
    if title:
        logger.opt(colors=True).info(f"<dim>{title}</dim>")
    
    logger.opt(colors=True).info(f"<dim>{sep}</dim>")
    
    # Header row
    header_row = "|" + "|".join(f" {h: <{widths[i]}} " for i, h in enumerate(headers)) + "|"
    logger.opt(colors=True).info(f"<bold>{header_row}</bold>")
    logger.opt(colors=True).info(f"<dim>{sep}</dim>")
    
    # Data rows
    for row in rows:
        data_row = "|" + "|".join(f" {str(row[i]) if i < len(row) else '': <{widths[i]}} " for i in range(len(headers))) + "|"
        logger.opt(colors=True).info(f"{data_row}")
    
    logger.opt(colors=True).info(f"<dim>{sep}</dim>")

