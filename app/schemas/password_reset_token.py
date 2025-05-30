from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class PasswordResetTokenCreate(BaseModel):
    user_id: UUID
    token: str
    expires_at: datetime

class PasswordResetTokenOut(BaseModel):
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    is_used: bool

    model_config = ConfigDict(from_attributes=True)