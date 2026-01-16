"""Storage service for uploads and outputs."""

import secrets
import time
from pathlib import Path

from loguru import logger

from ..settings import get_settings

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
        """
        Get the directory for a specific file_id.
        Invoked by: src/doc_generator/infrastructure/api/services/storage.py, src/doc_generator/infrastructure/storage/file_storage.py
        """
        return self.base_output_dir / file_id

    def _ensure_file_dirs(self, file_id: str) -> dict[str, Path]:
        """Ensure all subdirectories exist for a file_id.
        
        Returns:
            Dict with paths for source, images, pdf, pptx
        Invoked by: src/doc_generator/infrastructure/api/services/storage.py, src/doc_generator/infrastructure/storage/file_storage.py
        """
        file_dir = self._get_file_dir(file_id)
        dirs = {
            "root": file_dir,
            "source": file_dir / "source",
            "images": file_dir / "images",
            "pdf": file_dir / "pdf",
            "pptx": file_dir / "pptx",
            "markdown": file_dir / "markdown",
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

    def get_file_dirs(self, file_id: str) -> dict[str, Path]:
        """Get directory paths for a file_id.
        
        Args:
            file_id: File ID
            
        Returns:
            Dict with paths for root, source, images, pdf, pptx
        Invoked by: src/doc_generator/infrastructure/storage/file_storage.py
        """
        if file_id in self._uploads:
            return self._uploads[file_id]["dirs"]
        
        # Recreate dirs structure if needed
        return self._ensure_file_dirs(file_id)

    def get_output_dir(self, file_id: str, output_format: str) -> Path:
        """Get the output directory for a specific format.
        
        Args:
            file_id: File ID
            output_format: 'pdf' or 'pptx'
            
        Returns:
            Path to output directory
        Invoked by: (no references found)
        """
        dirs = self.get_file_dirs(file_id)
        return dirs.get(output_format, dirs["root"])

    def get_images_dir(self, file_id: str) -> Path:
        """
        Get the images directory for a file_id.
        Invoked by: (no references found)
        """
        dirs = self.get_file_dirs(file_id)
        return dirs["images"]

    def get_upload_content(self, file_id: str) -> bytes:
        """Get content of uploaded file.

        Args:
            file_id: File ID from save_upload

        Returns:
            File content bytes

        Raises:
            FileNotFoundError: If file_id not found
        Invoked by: tests/api/test_storage_service.py
        """
        path = self.get_upload_path(file_id)
        return path.read_bytes()

    def get_upload_metadata(self, file_id: str) -> dict:
        """Get metadata for uploaded file.

        Args:
            file_id: File ID from save_upload

        Returns:
            Metadata dict with filename, mime_type, path, created_at

        Raises:
            FileNotFoundError: If file_id not found
        Invoked by: (no references found)
        """
        if file_id not in self._uploads:
            # Try to reconstruct from disk
            try:
                path = self.get_upload_path(file_id)
                return {
                    "filename": path.name,
                    "path": path,
                    "file_id": file_id,
                }
            except FileNotFoundError:
                raise FileNotFoundError(f"Upload not found: {file_id}")
        return self._uploads[file_id].copy()

    def get_download_url(self, output_path: Path) -> str:
        """Generate download URL for output file.

        Args:
            output_path: Path to the output file

        Returns:
            Download URL with token
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

        # Use path relative to output root when possible to avoid collisions
        try:
            rel_path = output_path.relative_to(self.base_output_dir).as_posix()
            return f"{self.base_url}/{rel_path}?token={token}"
        except ValueError:
            pass

        # Fallback to just filename
        filename = output_path.name
        return f"{self.base_url}/{filename}?token={token}"

    def cleanup_upload(self, file_id: str) -> None:
        """Remove uploaded file and its directory.

        Args:
            file_id: File ID to remove
        Invoked by: src/doc_generator/infrastructure/storage/file_storage.py, tests/api/test_storage_service.py
        """
        import shutil
        
        if file_id in self._uploads:
            del self._uploads[file_id]
        
        file_dir = self._get_file_dir(file_id)
        if file_dir.exists():
            shutil.rmtree(file_dir)
            logger.info(f"Cleaned up: {file_dir}")

    def cleanup_expired_uploads(self, max_age_seconds: int = 3600) -> int:
        """Remove uploads older than max_age.

        Args:
            max_age_seconds: Maximum age in seconds (default 1 hour)

        Returns:
            Number of files cleaned up
        Invoked by: (no references found)
        """
        now = time.time()
        expired = []

        for file_id, metadata in self._uploads.items():
            if now - metadata["created_at"] > max_age_seconds:
                expired.append(file_id)

        for file_id in expired:
            self.cleanup_upload(file_id)

        return len(expired)

    # Legacy compatibility properties
    @property
    def upload_dir(self) -> Path:
        """
        Legacy: returns base output dir for backwards compatibility.
        Invoked by: src/doc_generator/infrastructure/api/services/generation.py
        """
        return self.base_output_dir

    @property
    def output_dir(self) -> Path:
        """
        Legacy: returns base output dir for backwards compatibility.
        Invoked by: .claude/skills/pdf/scripts/convert_pdf_to_images.py, .claude/skills/pptx/ooxml/scripts/unpack.py, .claude/skills/skill-creator/scripts/package_skill.py, scripts/batch_process_topics.py, scripts/generate_from_folder.py, src/doc_generator/application/nodes/generate_images.py, src/doc_generator/application/nodes/generate_output.py, src/doc_generator/application/workflow/nodes/generate_images.py, src/doc_generator/application/workflow/nodes/generate_output.py, src/doc_generator/utils/content_merger.py
        """
        return self.base_output_dir
