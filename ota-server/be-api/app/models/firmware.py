from sqlalchemy import Column, String, Text, BigInteger, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base


class Firmware(Base):
    __tablename__ = "firmwares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), unique=True, nullable=False)
    release_notes = Column(Text)
    file_path = Column(String(255), nullable=False)
    signature_path = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
