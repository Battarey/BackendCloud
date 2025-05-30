from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime

class FolderBase(BaseModel):
    name: str
    parent_id: Optional[UUID] = None

class FolderCreate(FolderBase):
    pass

class FolderOut(FolderBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)