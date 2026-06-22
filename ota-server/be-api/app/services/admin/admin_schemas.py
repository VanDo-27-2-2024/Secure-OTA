from uuid import UUID
from pydantic import BaseModel


class FirmwareUploadResponse(BaseModel):
    firmware_id: UUID
    version: str
    status: str
    checksum_sha256: str


class FirmwarePatchRequest(BaseModel):
    is_active: bool


class FirmwarePatchResponse(BaseModel):
    firmware_id: UUID
    is_active: bool
