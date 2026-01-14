"""File upload route."""

from fastapi import APIRouter, File, UploadFile

from ..schemas.responses import UploadResponse
from ..services.storage import StorageService

router = APIRouter(tags=["upload"])

# Shared storage service instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """
    Get or create storage service.
    Invoked by: src/doc_generator/infrastructure/api/routes/upload.py
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a source file",
    description=(
        "Upload a file to use as a generation source. Send a multipart form with "
        "a single `file` field. The response includes `file_id` to reference in "
        "`POST /api/generate`."
    ),
    response_description="Upload metadata including `file_id`.",
)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Upload a file for document generation.

    Args:
        file: The file to upload

    Returns:
        Upload response with file_id
    Invoked by: (no references found)
    """
    storage = get_storage_service()

    content = await file.read()
    # StorageService.save_upload: persist uploaded source and return file_id.
    file_id = storage.save_upload(
        content=content,
        filename=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
    )

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "unknown",
        size=len(content),
        mime_type=file.content_type or "application/octet-stream",
    )
