from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class UserSettingsCreate(BaseModel):
    storage_limit: Optional[int] = 1024*1024*1024  # 1GB
    theme: Optional[str] = "system"
    language: Optional[str] = "en"
    notifications_enabled: Optional[bool] = True

class UserSettingsOut(BaseModel):
    id: UUID
    user_id: UUID
    storage_limit: int
    theme: str
    language: str
    notifications_enabled: bool

    model_config = ConfigDict(from_attributes=True)