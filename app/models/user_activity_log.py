from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from app.db.database import Base
from app.db.types import GUID
import uuid
from datetime import datetime, timezone

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    action_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(255))

    __table_args__ = (
        Index("idx_user_activity_logs_user_id", "user_id"),
        Index("idx_user_activity_logs_action_time", "action_time"),
        Index("idx_user_activity_logs_user_action", "user_id", "action_type"),
        Index("idx_user_activity_logs_date_range", "action_time"),
    )