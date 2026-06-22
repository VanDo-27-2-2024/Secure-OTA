from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.services.admin import admin_service as service
from app.services.admin.admin_schemas import (
    FirmwarePatchRequest,
    FirmwarePatchResponse,
    FirmwareUploadResponse,
)

# TODO(security): Authentication for admin endpoints is handled at the API Gateway layer.
# All /admin/* routes MUST be protected by an auth middleware (e.g., JWT verification)
# before reaching this service. Do NOT expose these endpoints without authentication.

# TODO(security): Rate limiting should be applied at the API Gateway level.

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/firmware",
    response_model=FirmwareUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new firmware version",
)
async def upload_firmware(
    file: UploadFile = File(..., description="Firmware binary (.bin)"),
    version: str = Form(..., description="Semver version string, e.g. v1.2.0"),
    release_notes: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # Enforce file size limit (DoS / buffer overflow prevention)
    bin_data = await file.read()
    if len(bin_data) > settings.max_firmware_size_bytes:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_firmware_size_bytes} bytes",
        )

    firmware = await service.upload_firmware(version, release_notes, bin_data, db)
    return FirmwareUploadResponse(
        firmware_id=firmware.id,
        version=firmware.version,
        status="uploaded",
        checksum_sha256=firmware.checksum_sha256,
    )


@router.patch(
    "/firmware/{firmware_id}",
    response_model=FirmwarePatchResponse,
    summary="Activate or deactivate a firmware version",
)
async def patch_firmware(
    firmware_id: UUID,
    body: FirmwarePatchRequest,
    db: AsyncSession = Depends(get_db),
):
    firmware = await service.patch_firmware(firmware_id, body.is_active, db)
    return FirmwarePatchResponse(
        firmware_id=firmware.id,
        is_active=firmware.is_active,
    )
