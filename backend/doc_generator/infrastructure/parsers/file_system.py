"""
File system operations for document generator.

Provides utilities for file I/O, path resolution, and directory management.
"""

from pathlib import Path

from loguru import logger

from ...domain.exceptions import FileNotFoundError as DocGenFileNotFoundError


def ensure_directory(directory: Path) -> None:
    """
    Ensure directory exists, create if necessary.

    Args:
        directory: Path to directory

    Raises:
        PermissionError: If directory cannot be created
    Invoked by: src/doc_generator/infrastructure/parsers/file_system.py
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise


def validate_file_exists(file_path: Path) -> None:
    """
    Validate that file exists.

    Args:
        file_path: Path to file

    Raises:
        DocGenFileNotFoundError: If file does not exist
    Invoked by: src/doc_generator/application/parsers/markdown_parser.py, src/doc_generator/infrastructure/parsers/file_system.py
    """
    if not file_path.exists():
        raise DocGenFileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise DocGenFileNotFoundError(f"Path is not a file: {file_path}")


def get_file_extension(file_path: Path) -> str:
    """
    Get file extension (lowercase, without dot).

    Args:
        file_path: Path to file

    Returns:
        File extension (e.g., "pdf", "md")
    Invoked by: (no references found)
    """
    return file_path.suffix.lstrip(".").lower()


def resolve_path(path: str | Path, base_dir: Path | None = None) -> Path:
    """
    Resolve path to absolute path.

    Args:
        path: Path string or Path object
        base_dir: Base directory for relative paths

    Returns:
        Absolute Path object
    Invoked by: (no references found)
    """
    p = Path(path)

    if p.is_absolute():
        return p

    if base_dir is not None:
        return (base_dir / p).resolve()

    return p.resolve()


def read_text_file(file_path: Path, encoding: str = "utf-8") -> str:
    """
    Read text file content.

    Args:
        file_path: Path to text file
        encoding: File encoding

    Returns:
        File content as string

    Raises:
        DocGenFileNotFoundError: If file not found
        UnicodeDecodeError: If encoding is incorrect
    Invoked by: src/doc_generator/application/parsers/markdown_parser.py
    """
    validate_file_exists(file_path)

    try:
        content = file_path.read_text(encoding=encoding)
        logger.debug(f"Read {len(content)} characters from {file_path.name}")
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode {file_path} with encoding {encoding}: {e}")
        raise


def write_text_file(file_path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Write text content to file.

    Args:
        file_path: Path to output file
        content: Text content to write
        encoding: File encoding

    Raises:
        PermissionError: If file cannot be written
    Invoked by: (no references found)
    """
    try:
        # Ensure parent directory exists
        ensure_directory(file_path.parent)

        file_path.write_text(content, encoding=encoding)
        logger.info(f"Wrote {len(content)} characters to {file_path.name}")
    except Exception as e:
        logger.error(f"Failed to write {file_path}: {e}")
        raise
