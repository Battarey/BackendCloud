from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_settings import UserSettings
from uuid import UUID

# Creates new user settings
async def create_settings(
    session: AsyncSession, 
    settings_data: dict
):
    settings = UserSettings(**settings_data)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings

# Gets user settings by user ID
async def get_settings_by_user(
    session: AsyncSession, 
    user_id: UUID
):
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    return result.scalar_one_or_none()

# Updates user settings by user ID
async def update_settings(
    session: AsyncSession, 
    user_id: UUID, 
    update_data: dict
):
    settings = await get_settings_by_user(session, user_id)
    if not settings:
        return None
    for key, value in update_data.items():
        setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return settings

# Deletes user settings by user ID
async def delete_settings_by_user(
    session: AsyncSession, 
    user_id: UUID
):
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings:
        await session.delete(settings)
        await session.commit()