from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Boolean
from app.db.database import Base
from app.db.types import GUID
import uuid
from datetime import datetime, timezone

class File(Base):
    __tablename__ = "files"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    size = Column(BigInteger, nullable=False)
    folder_id = Column(GUID(), ForeignKey("folders.id"), nullable=True)
    content_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    path = Column(String, nullable=False)  # Key/path to MinIO
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_infected = Column(Boolean, default=False, nullable=False)