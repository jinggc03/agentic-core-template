"""Tests for Supabase Storage abstraction."""

import pytest

from app.integrations.supabase.storage import StorageServiceError, SupabaseStorageService


class FakeStorageBucket:
    def __init__(self):
        self.uploads = []

    def upload(self, path, data, file_options=None):
        self.uploads.append((path, data, file_options))
        return {"path": path}

    def download(self, path):
        return b"file-bytes"

    def create_signed_url(self, path, expires_in):
        return {"signedURL": f"https://example.test/{path}?expires={expires_in}"}


class FakeStorage:
    def __init__(self):
        self.bucket = FakeStorageBucket()

    def from_(self, _bucket):
        return self.bucket


class FakeClient:
    def __init__(self):
        self.storage = FakeStorage()


def test_storage_upload_download_and_signed_url():
    client = FakeClient()
    service = SupabaseStorageService(client=client)

    assert service.upload_bytes(
        bucket="agent-files",
        path="conv-1/input.pdf",
        data=b"file",
        content_type="application/pdf",
        upsert=True,
    ) == {"path": "conv-1/input.pdf"}
    assert service.download_bytes(bucket="agent-files", path="conv-1/input.pdf") == b"file-bytes"
    assert service.create_signed_url(bucket="agent-files", path="conv-1/input.pdf") == (
        "https://example.test/conv-1/input.pdf?expires=3600"
    )
    assert client.storage.bucket.uploads[0][2] == {
        "upsert": "true",
        "content-type": "application/pdf",
    }


def test_storage_signed_url_requires_url_response():
    class MissingUrlBucket(FakeStorageBucket):
        def create_signed_url(self, _path, _expires_in):
            return {}

    client = FakeClient()
    client.storage.bucket = MissingUrlBucket()
    service = SupabaseStorageService(client=client)

    with pytest.raises(StorageServiceError, match="signed URL"):
        service.create_signed_url(bucket="agent-files", path="missing.txt")
