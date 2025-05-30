from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class FileBase(BaseModel):
    filename: str
    size: int
    folder_id: Optional[UUID] = None
    content_type: str

class FileCreate(FileBase):
    pass

class FileOut(FileBase):
    id: UUID
    user_id: UUID
    uploaded_at: datetime
    path: str
    is_deleted: bool
    deleted_at: Optional[datetime]
    is_infected: bool
    model_config = ConfigDict(from_attributes=True)

class InitiateUploadRequest(BaseModel):
    filename: str
    size: int
    folder_id: Optional[UUID] = None
    content_type: str

class InitiateUploadResponse(BaseModel):
    upload_id: str
    object_name: str

class UploadChunkRequest(BaseModel):
    upload_id: str
    object_name: str
    part_number: int
    chunk: bytes

class CompleteUploadPart(BaseModel):
    part_number: int
    etag: str

class CompleteUploadRequest(BaseModel):
    upload_id: str
    object_name: str
    parts: List[CompleteUploadPart]

class FileStats(BaseModel):
    total_files: int
    total_size: int