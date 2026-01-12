"""Tests for storage service."""

import pytest
from pathlib import Path

from doc_generator.infrastructure.api.services.storage import StorageService


@pytest.fixture
def storage_service(tmp_path):
    """
    Create storage service with temp directories.
    Invoked by: src/doc_generator/infrastructure/api/services/generation.py, tests/api/test_storage_service.py
    """
    return StorageService(
        upload_dir=tmp_path / "uploads",
        output_dir=tmp_path / "outputs",
    )


class TestStorageService:
    """Test storage service."""

    def test_save_upload(self, storage_service):
        """
        Invoked by: (no references found)
        """
        content = b"test file content"
        file_id = storage_service.save_upload(
            content=content,
            filename="test.pdf",
            mime_type="application/pdf",
        )
        assert file_id.startswith("f_")
        assert storage_service.get_upload_path(file_id).exists()

    def test_get_upload_content(self, storage_service):
        """
        Invoked by: (no references found)
        """
        content = b"test content"
        file_id = storage_service.save_upload(
            content=content,
            filename="test.txt",
            mime_type="text/plain",
        )
        retrieved = storage_service.get_upload_content(file_id)
        assert retrieved == content

    def test_get_nonexistent_upload(self, storage_service):
        """
        Invoked by: (no references found)
        """
        with pytest.raises(FileNotFoundError):
            storage_service.get_upload_content("f_nonexistent")

    def test_save_output(self, storage_service):
        """
        Invoked by: (no references found)
        """
        content = b"generated pdf content"
        output_path = storage_service.save_output(
            content=content,
            filename="output.pdf",
        )
        assert output_path.exists()
        assert output_path.read_bytes() == content

    def test_get_download_url(self, storage_service):
        """
        Invoked by: (no references found)
        """
        content = b"pdf content"
        output_path = storage_service.save_output(
            content=content,
            filename="doc.pdf",
        )
        url = storage_service.get_download_url(output_path)
        assert "doc" in url and ".pdf" in url

    def test_cleanup_expired(self, storage_service):
        """
        Invoked by: (no references found)
        """
        file_id = storage_service.save_upload(
            content=b"temp",
            filename="temp.txt",
            mime_type="text/plain",
        )
        path = storage_service.get_upload_path(file_id)
        assert path.exists()
        storage_service.cleanup_upload(file_id)
        assert not path.exists()
