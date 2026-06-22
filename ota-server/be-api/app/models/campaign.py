import enum
from sqlalchemy import Column, Text, DateTime, Enum as SAEnum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import Base


class UpdateState(str, enum.Enum):
    pending = "pending"
    downloading = "downloading"
    installing = "installing"
    success = "success"
    failed = "failed"
    rolled_back = "rolled_back"


class DeviceUpdateLog(Base):
    __tablename__ = "device_update_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    firmware_id = Column(UUID(as_uuid=True), ForeignKey("firmwares.id"), nullable=False)
    status = Column(SAEnum(UpdateState, name="update_state"), default=UpdateState.pending)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    device = relationship("Device")
    firmware = relationship("Firmware")
