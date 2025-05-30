from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.password_reset_token import PasswordResetToken
from datetime import datetime

# Creates a new password reset token
async def create_reset_token(
    session: AsyncSession, 
    data: dict
):
    token = PasswordResetToken(**data)
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token

# Gets the password reset token by its string value
async def get_by_token(
    session: AsyncSession, 
    token_str: str
):
    result = await session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token_str)
    )
    return result.scalar_one_or_none()

# Marks the token as used
async def mark_token_used(
    session: AsyncSession, 
    token_str: str
):
    token = await get_by_token(session, token_str)
    if token:
        token.is_used = True
        await session.commit()
        await session.refresh(token)
    return token

# Gets a valid (unused and unexpired) token
async def get_valid_token(
    session: AsyncSession, 
    token_str: str, 
    now: datetime
):
    result = await session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token_str,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > now
        )
    )
    return result.scalar_one_or_none()