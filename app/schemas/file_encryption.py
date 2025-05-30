from pydantic import BaseModel
from uuid import UUID

class FileEncryptionOut(BaseModel):
    file_id: UUID
    encryption_salt: bytes
    encryption_iv: bytes