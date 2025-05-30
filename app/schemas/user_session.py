from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserSessionCreate(BaseModel):
    device_info: Optional[dict] = None

class UserSessionOut(BaseModel):
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    device_info: Optional[dict]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)