from sqlalchemy import Column, ForeignKey, LargeBinary
from app.db.types import GUID
from app.db.database import Base
import uuid

class FileEncryption(Base):
    __tablename__ = "file_encryption"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    file_id = Column(GUID(), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, unique=True)
    encryption_salt = Column(LargeBinary, nullable=False)
    encryption_iv = Column(LargeBinary, nullable=False)