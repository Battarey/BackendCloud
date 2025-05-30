from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.password_reset_token import PasswordResetTokenCreate, PasswordResetTokenOut
from app.repositories.password_reset_token_repo import create_reset_token, get_by_token, mark_token_used, get_valid_token
from datetime import datetime, timezone
from fastapi_limiter.depends import RateLimiter

router = APIRouter(
    prefix="/reset_tokens",
    tags=["reset_tokens"]
)

@router.post("/", response_model=PasswordResetTokenOut, description="Generate a new password reset token. Accepts the user's email and returns the generated token.", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_token(
    data: PasswordResetTokenCreate,
    db: AsyncSession = Depends(get_db)
):
    return await create_reset_token(db, data.model_dump())

@router.get("/{token}", response_model=PasswordResetTokenOut, description="Get password reset token information by its value.")
async def get_token(
    token: str, 
    db: AsyncSession = Depends(get_db)
):
    token_obj = await get_by_token(db, token)
    if not token_obj:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_obj

@router.post("/{token}/use", response_model=PasswordResetTokenOut, description="Mark the password reset token as used.")
async def use_token(
    token: str, 
    db: AsyncSession = Depends(get_db)
):
    token_obj = await mark_token_used(db, token)
    if not token_obj:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_obj

@router.get("/{token}/valid", response_model=PasswordResetTokenOut, description="Check if the password reset token is valid (not expired or used).")
async def check_token_valid(
    token: str, 
    db: AsyncSession = Depends(get_db)
):
    token_obj = await get_valid_token(db, token, datetime.now(timezone.utc))
    if not token_obj:
        raise HTTPException(status_code=404, detail="Token is invalid or expired")
    return token_obj