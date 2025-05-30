from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from app.db.database import Base
from app.db.types import GUID
import uuid
from datetime import datetime, timezone

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False, index=True)

    __table_args__ = (
        Index("idx_password_reset_tokens_user_id", "user_id"),
        Index("idx_password_reset_tokens_token", "token"),
        Index("idx_password_reset_tokens_expires", "expires_at"),
        Index("idx_unused_reset_tokens", "is_used"),
    )