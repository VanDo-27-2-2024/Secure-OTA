import hashlib
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import kms_client, storage_client
from app.models.firmware import Firmware

logger = logging.getLogger(__name__)


async def upload_firmware(
    version: str,
    release_notes: str | None,
    bin_data: bytes,
    db: AsyncSession,
) -> Firmware:
    """
    Full upload flow:
    1. Check version uniqueness
    2. Compute SHA256
    3. Sign via KMS
    4. Save to local storage
    5. Insert DB row
    """
    # 1. Validate version uniqueness
    existing = await db.execute(
        select(Firmware).where(Firmware.version == version)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Firmware version '{version}' already exists",
        )

    # 2. Compute SHA256 checksum
    checksum = hashlib.sha256(bin_data).hexdigest()

    # 3. Call KMS to sign — raises 502 if KMS is down
    signature_hex = await kms_client.sign_firmware(bin_data)

    # 4. Save binary + signature to local storage
    file_path, sig_path = storage_client.save_firmware(version, bin_data, signature_hex)

    # 5. Insert into DB
    firmware = Firmware(
        version=version,
        release_notes=release_notes,
        file_path=file_path,
        signature_path=sig_path,
        file_size=len(bin_data),
        checksum_sha256=checksum,
        is_active=True,
    )
    db.add(firmware)
    await db.flush()  # get generated UUID before commit
    await db.refresh(firmware)

    logger.info("Firmware uploaded: version=%s id=%s", version, firmware.id)
    return firmware


async def patch_firmware(
    firmware_id: UUID,
    is_active: bool,
    db: AsyncSession,
) -> Firmware:
    """Activate or deactivate a firmware version."""
    result = await db.execute(
        select(Firmware).where(Firmware.id == firmware_id)
    )
    firmware = result.scalar_one_or_none()
    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware not found",
        )

    firmware.is_active = is_active
    await db.flush()
    await db.refresh(firmware)

    logger.info("Firmware patched: id=%s is_active=%s", firmware_id, is_active)
    return firmware
