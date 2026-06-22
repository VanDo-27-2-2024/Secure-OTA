from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage_client
from app.db.session import get_db
from app.models.firmware import Firmware
from app.services.device import device_service as service
from app.services.device.device_schemas import (
    CreateLogRequest,
    CreateLogResponse,
    LatestFirmwareResponse,
    RegisterRequest,
    RegisterResponse,
    UpdateLogRequest,
    UpdateLogResponse,
)
from sqlalchemy import select

# TODO(security): Authentication for /device/* endpoints is handled at the API Gateway.
# Each device should present a valid token (e.g., device certificate or API key) verified
# at the gateway before requests reach this service.

# TODO(security): Rate limiting should be applied at the API Gateway to prevent
# a rogue device from flooding the server with requests.

router = APIRouter(prefix="/device", tags=["device"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_200_OK,
    summary="Register or update a device (upsert)",
)
async def register_device(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    device = await service.register_device(
        body.device_id, body.current_firmware_version, db
    )
    return RegisterResponse(id=device.id, device_id=device.device_id)


@router.get(
    "/latest",
    response_model=LatestFirmwareResponse,
    summary="Check if a newer firmware version is available",
)
async def get_latest(
    current_version: str,
    db: AsyncSession = Depends(get_db),
):
    firmware = await service.get_latest_firmware(current_version, db)
    if firmware is None:
        return LatestFirmwareResponse(update_available=False)

    return LatestFirmwareResponse(
        update_available=True,
        firmware_id=firmware.id,
        version=firmware.version,
        checksum_sha256=firmware.checksum_sha256,
        download_url=f"/device/firmware/{firmware.version}",
    )


@router.get(
    "/firmware/{version}",
    summary="Download firmware binary for a specific version",
)
async def download_firmware(
    version: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Streams the firmware binary.
    - 404 if version not found
    - 403 if firmware is deactivated/revoked
    """
    result = await db.execute(
        select(Firmware).where(Firmware.version == version)
    )
    firmware = result.scalar_one_or_none()

    if firmware is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Firmware version '{version}' not found",
        )

    if not firmware.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Firmware version '{version}' is inactive (revoked)",
        )

    try:
        bin_data = storage_client.read_firmware_bytes(firmware.file_path)
        sig_hex = storage_client.read_signature_hex(firmware.signature_path)
    except (FileNotFoundError, ValueError) as exc:
        # Do not leak internal path details to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firmware file unavailable",
        ) from exc

    return StreamingResponse(
        content=iter([bin_data]),
        media_type="application/octet-stream",
        headers={
            "X-Firmware-Signature": sig_hex,
            "Content-Disposition": "attachment; filename=firmware.bin",
            "X-Content-Type-Options": "nosniff",
            "Content-Length": str(len(bin_data)),
        },
    )


@router.post(
    "/update-log",
    response_model=CreateLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new update attempt log entry",
)
async def create_update_log(
    body: CreateLogRequest,
    db: AsyncSession = Depends(get_db),
):
    log = await service.create_update_log(body.device_id, body.firmware_id, db)
    return CreateLogResponse(log_id=log.id, status=log.status.value)


@router.patch(
    "/update-log/{log_id}",
    response_model=UpdateLogResponse,
    summary="Report progress or final result of an update",
)
async def update_log(
    log_id: UUID,
    body: UpdateLogRequest,
    db: AsyncSession = Depends(get_db),
):
    log = await service.update_log_status(log_id, body.status, body.error_message, db)
    return UpdateLogResponse(log_id=log.id, status=log.status.value)
