from sqlalchemy import Column, String, DateTime, Boolean, Integer, Index, Enum
from app.db.database import Base
from app.db.types import GUID
import uuid
import enum
from datetime import datetime, timezone

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index("idx_users_locked_until", "locked_until"),
    )