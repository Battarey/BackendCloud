from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserActivityLogCreate(BaseModel):
    action_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserActivityLogOut(BaseModel):
    id: UUID
    user_id: UUID
    action_type: str
    action_time: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]

    model_config = ConfigDict(from_attributes=True)