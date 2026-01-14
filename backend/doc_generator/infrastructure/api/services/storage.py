"""Storage service for uploads and outputs."""

import secrets
import time
from pathlib import Path

from loguru import logger

from ...settings import get_settings

class StorageService:
    """Manages uploads and generated outputs with organized folder structure.
    
    Directory structure:
        data/output/
            <file_id>/
                source/      - Original uploaded files
                images/      - Generated images
                pdf/         - Generated PDF files
                pptx/        - Generated PPTX files
            cache/           - Cache metadata files
    """

    def __init__(
        self,
        base_output_dir: Path | None = None,
        cache_dir: Path | None = None,
        base_url: str = "/api/download",
    ):
        """Initialize storage service.

        Args:
            base_output_dir: Base directory for all outputs
            base_url: Base URL for download links
        Invoked by: (no references found)
        """
        settings = get_settings()
        if base_output_dir is None:
            base_output_dir = settings.generator.output_dir
        if cache_dir is None:
            cache_dir = settings.generator.cache_dir

        self.base_output_dir = Path(base_output_dir)
        self.cache_dir = Path(cache_dir)
        self.base_url = base_url

        # Ensure base directories exist
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Track upload metadata
        self._uploads: dict[str, dict] = {}

    def _get_file_dir(self, file_id: str) -> Path:
        """Get the directory for a specific file_id.

        Used by: save_upload, get_upload_path.
        Invoked by: src/doc_generator/infrastructure/api/services/storage.py, src/doc_generator/infrastructure/storage/file_storage.py
        """
        return self.base_output_dir / file_id

    def _ensure_file_dirs(self, file_id: str) -> dict[str, Path]:
        """Ensure all subdirectories exist for a file_id.
        
        Returns:
            Dict with paths for source, images, pdf, pptx

        Used by: save_upload.
        Invoked by: src/doc_generator/infrastructure/api/services/storage.py, src/doc_generator/infrastructure/storage/file_storage.py
        """
        file_dir = self._get_file_dir(file_id)
        dirs = {
            "root": file_dir,
            "source": file_dir / "source",
            "images": file_dir / "images",
            "pdf": file_dir / "pdf",
            "pptx": file_dir / "pptx",
        }
        for d in dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        return dirs

    def save_upload(
        self,
        content: bytes,
        filename: str,
        mime_type: str,
    ) -> str:
        """Save uploaded file and return file_id.

        Creates organized folder structure:
        data/output/<file_id>/source/<original_filename>

        Args:
            content: File content bytes
            filename: Original filename
            mime_type: MIME type of file

        Returns:
            Unique file ID (f_...)

        Used by: src/doc_generator/infrastructure/api/routes/upload.py
        Invoked by: src/doc_generator/infrastructure/api/routes/upload.py, tests/api/test_storage_service.py
        """
        file_id = f"f_{secrets.token_hex(12)}"
        dirs = self._ensure_file_dirs(file_id)
        
        # Save to source directory with original filename
        storage_path = dirs["source"] / filename

        storage_path.write_bytes(content)
        logger.info(f"Saved upload: {storage_path}")

        self._uploads[file_id] = {
            "filename": filename,
            "mime_type": mime_type,
            "path": storage_path,
            "file_id": file_id,
            "dirs": dirs,
            "created_at": time.time(),
        }

        return file_id

    def get_upload_path(self, file_id: str) -> Path:
        """Get path to uploaded file.

        Args:
            file_id: File ID from save_upload

        Returns:
            Path to the file

        Raises:
            FileNotFoundError: If file_id not found

        Used by: src/doc_generator/infrastructure/api/services/generation.py
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py, src/doc_generator/infrastructure/storage/file_storage.py, tests/api/test_storage_service.py
        """
        if file_id in self._uploads:
            return self._uploads[file_id]["path"]
        
        # Try to find on disk if not in memory (after server restart)
        file_dir = self._get_file_dir(file_id)
        source_dir = file_dir / "source"
        if source_dir.exists():
            files = list(source_dir.iterdir())
            if files:
                return files[0]
        
        raise FileNotFoundError(f"Upload not found: {file_id}")


    def get_download_url(self, output_path: Path) -> str:
        """Generate download URL for output file.

        Args:
            output_path: Path to the output file

        Returns:
            Download URL with token

        Used by: src/doc_generator/infrastructure/api/services/generation.py,
                 src/doc_generator/infrastructure/api/routes/generate.py
        Invoked by: src/doc_generator/infrastructure/api/routes/generate.py, src/doc_generator/infrastructure/api/services/generation.py, tests/api/test_storage_service.py
        """
        # Generate a simple token (in production, use signed URLs)
        token = secrets.token_urlsafe(16)
        
        # Try to extract file_id and create a cleaner URL
        parts = output_path.parts
        for i, part in enumerate(parts):
            if part.startswith("f_"):
                # Found file_id, construct relative path from there
                rel_path = "/".join(parts[i:])
                return f"{self.base_url}/{rel_path}?token={token}"
        
        # Fallback to just filename
        filename = output_path.name
        return f"{self.base_url}/{filename}?token={token}"

    # Legacy compatibility properties
    @property
    def upload_dir(self) -> Path:
        """Legacy: returns base output dir for backwards compatibility.

        Used by: src/doc_generator/infrastructure/api/services/generation.py
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        return self.base_output_dir
