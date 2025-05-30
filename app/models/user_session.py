from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index, JSON
from app.db.database import Base
from app.db.types import GUID
import uuid
from datetime import datetime, timezone

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    device_info = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_token", "token"),
        Index("idx_user_sessions_expires_at", "expires_at"),
        Index("idx_user_sessions_user_active", "user_id", "is_active"),
        Index("idx_active_sessions", "is_active"),
    )