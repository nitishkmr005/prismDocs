"""File download route for generated documents."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

router = APIRouter(tags=["download"])

# Base output directory
OUTPUT_BASE = Path("src/output")


def find_file(file_path: str) -> Path | None:
    """Find a file in the output directory.

    Supports:
    - Direct filename: "document.pdf"
    - Nested path: "f_abc123/pdf/document.pdf"

    Args:
        file_path: Path to the file (can be nested)

    Returns:
        Path to the file if found, None otherwise
    Invoked by: src/doc_generator/infrastructure/api/routes/download.py
    """
    # Try as a nested path first
    full_path = OUTPUT_BASE / file_path
    if full_path.exists() and full_path.is_file():
        return full_path

    # Try just the filename in various locations
    filename = Path(file_path).name
    
    # Search recursively for the file
    for match in OUTPUT_BASE.rglob(filename):
        if match.is_file():
            return match

    return None


@router.get(
    "/download/{file_path:path}",
    summary="Download a generated document",
    description=(
        "Download a generated file by its `file_path` (from the generate response). "
        "Example: `/api/download/f_abc123/pdf/output.pdf`. The optional `token` "
        "query param is accepted for future auth."
    ),
    response_description="The generated file as a streamed response.",
)
async def download_file(file_path: str, token: str | None = None) -> FileResponse:
    """Download a generated document.

    Supports nested paths like:
    - /api/download/document.pdf
    - /api/download/f_abc123/pdf/document.pdf

    Args:
        file_path: Path to the file (can be nested)
        token: Optional access token (for future auth)

    Returns:
        FileResponse with the document

    Raises:
        HTTPException: If file not found
    Invoked by: (no references found)
    """
    logger.info(f"Download requested: {file_path}")

    # Find the file
    found_path = find_file(file_path)

    if not found_path:
        logger.warning(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}",
        )

    # Determine media type
    suffix = found_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".md": "text/markdown",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    logger.info(f"Serving file: {found_path} ({media_type})")

    return FileResponse(
        path=found_path,
        filename=found_path.name,
        media_type=media_type,
    )
