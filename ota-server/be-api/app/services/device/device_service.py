import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from packaging.version import Version, InvalidVersion
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import DeviceUpdateLog, UpdateState
from app.models.device import Device
from app.models.firmware import Firmware

logger = logging.getLogger(__name__)

# Terminal states — when reached, set completed_at
_TERMINAL_STATES = {UpdateState.success, UpdateState.failed, UpdateState.rolled_back}


async def register_device(
    device_id: str,
    current_firmware_version: str | None,
    db: AsyncSession,
) -> Device:
    """Upsert device — insert on first contact, update version+last_seen on subsequent calls."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()

    if device is None:
        device = Device(
            device_id=device_id,
            current_firmware_version=current_firmware_version,
            last_seen=now,
        )
        db.add(device)
        logger.info("New device registered: device_id=%s", device_id)
    else:
        device.current_firmware_version = current_firmware_version
        device.last_seen = now
        logger.info("Device updated: device_id=%s", device_id)

    await db.flush()
    await db.refresh(device)
    return device


async def get_latest_firmware(
    current_version: str,
    db: AsyncSession,
) -> Firmware | None:
    """
    Return the latest active firmware if it is newer than current_version.
    Version comparison uses semver (packaging.version.Version).
    Returns None if device is already up to date or no active firmware exists.
    """
    result = await db.execute(
        select(Firmware)
        .where(Firmware.is_active == True)  # noqa: E712
        .order_by(Firmware.created_at.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    if latest is None:
        return None

    # Semver comparison — fall back to string compare if versions are not PEP-440 compliant
    try:
        if Version(latest.version) <= Version(current_version):
            return None
    except InvalidVersion:
        if latest.version <= current_version:
            return None

    return latest


async def create_update_log(
    device_id_str: str,
    firmware_id: UUID,
    db: AsyncSession,
) -> DeviceUpdateLog:
    """Resolve device UUID from device_id string, then insert a new update log."""
    # Resolve device
    dev_result = await db.execute(
        select(Device).where(Device.device_id == device_id_str)
    )
    device = dev_result.scalar_one_or_none()
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id_str}' not found. Please register first.",
        )

    # Verify firmware exists
    fw_result = await db.execute(
        select(Firmware).where(Firmware.id == firmware_id)
    )
    if fw_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Firmware not found",
        )

    log = DeviceUpdateLog(
        device_id=device.id,
        firmware_id=firmware_id,
        status=UpdateState.pending,
        started_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)

    logger.info("Update log created: log_id=%s device_id=%s firmware_id=%s", log.id, device_id_str, firmware_id)
    return log


async def update_log_status(
    log_id: UUID,
    new_status: UpdateState,
    error_message: str | None,
    db: AsyncSession,
) -> DeviceUpdateLog:
    """Update log status, set completed_at for terminal states, update device version on success."""
    result = await db.execute(
        select(DeviceUpdateLog).where(DeviceUpdateLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update log not found",
        )

    log.status = new_status
    log.error_message = error_message

    now = datetime.now(timezone.utc)
    if new_status in _TERMINAL_STATES:
        log.completed_at = now

    # If success → update device's current firmware version
    if new_status == UpdateState.success:
        fw_result = await db.execute(
            select(Firmware).where(Firmware.id == log.firmware_id)
        )
        firmware = fw_result.scalar_one_or_none()

        dev_result = await db.execute(
            select(Device).where(Device.id == log.device_id)
        )
        device = dev_result.scalar_one_or_none()

        if firmware and device:
            device.current_firmware_version = firmware.version
            device.last_seen = now
            logger.info(
                "Device firmware updated on success: device_id=%s new_version=%s",
                device.device_id,
                firmware.version,
            )

    await db.flush()
    await db.refresh(log)
    return log
