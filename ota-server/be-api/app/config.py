import os
import secrets
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database — MUST be set via env var, no hardcoded fallback
    database_url: str

    # KMS service URL — MUST be set via env var
    kms_url: str

    # Base path for firmware file storage
    storage_base_path: str = "/storage"

    # Max firmware file size: 100 MB
    max_firmware_size_bytes: int = 100 * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context):
        # Fail fast if critical vars are missing
        if not self.database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        if not self.kms_url:
            raise RuntimeError("KMS_URL environment variable is required")


settings = Settings()
