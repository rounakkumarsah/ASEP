"""
ASEP — Cloudinary Cloud Storage Service
=======================================
Serverless-compatible file & image upload helper.
Reads CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET
via environment variables without hardcoded credentials.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class CloudinaryStorageService:
    """Cloudinary file upload service for Vercel serverless persistence."""

    def __init__(self) -> None:
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET")

        if self.cloud_name and self.api_key and self.api_secret:
            try:
                import cloudinary
                cloudinary.config(
                    cloud_name=self.cloud_name,
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    secure=True,
                )
                logger.info("Cloudinary storage service configured successfully.")
            except Exception as exc:
                logger.warning("Cloudinary configuration failed: %s", exc)

    async def upload_file(self, file_bytes: bytes, filename: str, folder: str = "asep_uploads") -> dict[str, Any]:
        """Upload file bytes to Cloudinary and return secure URL metadata.

        Raises:
            RuntimeError: If Cloudinary credentials are not configured.
        """
        if not (self.cloud_name and self.api_key and self.api_secret):
            raise RuntimeError(
                "File storage is not configured. "
                "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET "
                "environment variables to enable file uploads."
            )

        try:
            import cloudinary.uploader
            response = cloudinary.uploader.upload(
                file_bytes,
                public_id=f"{folder}/{filename}",
                resource_type="auto",
            )
            logger.info("Uploaded %s to Cloudinary: %s", filename, response.get("secure_url"))
            return {
                "secure_url": response.get("secure_url"),
                "public_id": response.get("public_id"),
                "bytes": response.get("bytes", len(file_bytes)),
                "is_mock": False,
            }
        except Exception as exc:
            logger.error("Cloudinary upload failed for %s: %s", filename, exc)
            raise RuntimeError(f"File upload failed: {exc}") from exc



def upload_to_cloudinary(file_bytes: bytes, resource_type: str = "image", filename: str | None = None) -> str | None:
    """
    Upload file bytes to Cloudinary and return secure URL.
    Reads CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET
    strictly via os.getenv without hardcoded values.
    """
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not (cloud_name and api_key and api_secret):
        logger.warning("Cloudinary environment variables not set — fallback to local in-memory processing.")
        return None

    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        response = cloudinary.uploader.upload(
            file_bytes,
            resource_type=resource_type,
            public_id=f"asep_uploads/{filename}" if filename else None,
        )
        url = response.get("secure_url")
        logger.info("Cloudinary upload successful: %s", url)
        return url
    except Exception as exc:
        logger.error("Cloudinary upload error: %s", exc)
        return None

