from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.user import UserRole

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]{};:,.<>/?\\|" for c in v):
            raise ValueError("The password must contain at least one special character.")
        return v

class UserOut(UserBase):
    id: UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    role: UserRole

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str
    password: str

class UserDelete(BaseModel):
    username: str
    password: str
