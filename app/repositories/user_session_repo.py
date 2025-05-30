from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_session import UserSession
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

# Creates a new user session with a token and expiration time
async def create_session(
    session: AsyncSession, 
    user_id: UUID, 
    device_info=None, 
    expires_minutes=60
):
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)
    user_session = UserSession(
        user_id=user_id,
        token=token,
        created_at=now,
        expires_at=expires_at,
        device_info=device_info,
        is_active=True
    )
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)
    return user_session

# Gets all active sessions of a user
async def get_active_sessions_by_user(
    session: AsyncSession, 
    user_id: UUID
):
    result = await session.execute(
        select(UserSession).where(UserSession.user_id == user_id, UserSession.is_active == True)
    )
    return result.scalars().all()

# Gets a session by token
async def get_session_by_token(
    session: AsyncSession, 
    token
):
    result = await session.execute(
        select(UserSession).where(UserSession.token == token)
    )
    return result.scalar_one_or_none()

# Deactivates a session by token
async def deactivate_session(
    session: AsyncSession, 
    token
):
    user_session = await get_session_by_token(session, token)
    if user_session:
        user_session.is_active = False
        await session.commit()
        return True
    return False