from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.db.types import GUID
from uuid import uuid4
from datetime import datetime

class Folder(Base):
    __tablename__ = "folders"

    id = Column(GUID(), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    parent_id = Column(GUID(), ForeignKey("folders.id"), nullable=True)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=False), default=lambda: datetime.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), default=lambda: datetime.now(), onupdate=lambda: datetime.now(), nullable=False)

    parent = relationship("Folder", remote_side=[id], backref="subfolders")