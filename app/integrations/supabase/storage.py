"""Supabase Storage abstraction."""

from typing import Any, Optional

from app.integrations.supabase.client import get_supabase_service_client


class StorageServiceError(RuntimeError):
    """Raised when storage operations fail."""


class SupabaseStorageService:
    """Small service wrapper around Supabase Storage.

    Agents should depend on this abstraction or a higher-level file service,
    never on Supabase Storage SDK calls directly.
    """

    def __init__(self, client: Any | None = None):
        self.client = client or get_supabase_service_client()

    def upload_bytes(
        self,
        *,
        bucket: str,
        path: str,
        data: bytes,
        content_type: Optional[str] = None,
        upsert: bool = False,
    ) -> Any:
        """Upload bytes to a Supabase Storage bucket."""
        options: dict[str, Any] = {"upsert": str(upsert).lower()}
        if content_type:
            options["content-type"] = content_type
        return self._bucket(bucket).upload(path, data, file_options=options)

    def download_bytes(self, *, bucket: str, path: str) -> bytes:
        """Download bytes from Supabase Storage."""
        result = self._bucket(bucket).download(path)
        if isinstance(result, bytes):
            return result
        if hasattr(result, "read"):
            return result.read()
        raise StorageServiceError("Supabase Storage download did not return bytes.")

    def create_signed_url(
        self,
        *,
        bucket: str,
        path: str,
        expires_in: int = 3600,
    ) -> str:
        """Create a temporary signed URL for a private object."""
        response = self._bucket(bucket).create_signed_url(path, expires_in)
        data = getattr(response, "data", response)
        if isinstance(data, dict):
            signed_url = data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")
            if signed_url:
                return signed_url
        raise StorageServiceError("Supabase Storage did not return a signed URL.")

    def _bucket(self, bucket: str) -> Any:
        return self.client.storage.from_(bucket)
