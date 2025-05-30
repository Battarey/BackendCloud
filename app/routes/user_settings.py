from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user_settings import UserSettingsCreate, UserSettingsOut
from app.repositories.user_settings_repo import create_settings, get_settings_by_user, update_settings, delete_settings_by_user
from app.core.security import get_current_user
from uuid import UUID


router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)

@router.post("/", response_model=UserSettingsOut, description="Create User Preferences. Accepts preference parameters and returns the created preferences.")
async def create_user_settings(
    settings: UserSettingsCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Force user_id to be used from current_user
    settings_data = settings.model_dump()
    settings_data["user_id"] = current_user.id
    return await create_settings(db, settings_data)

@router.get("/user/me", response_model=UserSettingsOut, description="Get current user's settings. Returns settings if they exist.")
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    settings = await get_settings_by_user(db, current_user.id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.put("/user/me", response_model=UserSettingsOut, description="Update current user's settings. Accepts new parameters and returns updated settings.")
async def update_user_settings(
    update_data: UserSettingsCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    settings = await update_settings(db, current_user.id, update_data.model_dump(exclude_unset=True))
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings

@router.delete("/user/me", description="Delete current user's settings")
async def delete_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    settings = await get_settings_by_user(db, current_user.id)
    if not settings:
        return {"detail": "Settings not found"}
    await db.delete(settings)
    await db.commit()
    return {"detail": "Settings deleted"}

@router.delete("/user/{user_id}", description="Delete settings of a specific user")
async def delete_user_settings_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    await delete_settings_by_user(db, user_id)
    return {"detail": "User settings deleted"}