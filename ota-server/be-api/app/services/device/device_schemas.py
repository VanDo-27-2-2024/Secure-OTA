from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.models.campaign import UpdateState


# --- POST /device/register ---
class RegisterRequest(BaseModel):
    device_id: str
    current_firmware_version: Optional[str] = None


class RegisterResponse(BaseModel):
    id: UUID
    device_id: str


# --- GET /device/latest ---
class LatestFirmwareResponse(BaseModel):
    update_available: bool
    firmware_id: Optional[UUID] = None
    version: Optional[str] = None
    checksum_sha256: Optional[str] = None
    download_url: Optional[str] = None


# --- POST /device/update-log ---
class CreateLogRequest(BaseModel):
    device_id: str
    firmware_id: UUID
    status: str = "pending"


class CreateLogResponse(BaseModel):
    log_id: UUID
    status: str


# --- PATCH /device/update-log/{log_id} ---
class UpdateLogRequest(BaseModel):
    status: UpdateState
    error_message: Optional[str] = None


class UpdateLogResponse(BaseModel):
    log_id: UUID
    status: str
