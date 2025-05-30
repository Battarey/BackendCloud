from sqlalchemy import Column, String, BigInteger, Boolean, ForeignKey, Index
from app.db.database import Base
from app.db.types import GUID
import uuid

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    storage_limit = Column(BigInteger, nullable=False, default=1024*1024*1024)  # 1GB by default
    theme = Column(String(20), nullable=False, default="system")
    language = Column(String(10), nullable=False, default="en")
    notifications_enabled = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_user_settings_user_id", "user_id"),
    )