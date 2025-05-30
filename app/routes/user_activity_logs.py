from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user_activity_log import UserActivityLogCreate, UserActivityLogOut
from app.repositories.user_activity_log_repo import create_log, get_logs_by_user, get_logs_by_date_range
from app.core.security import get_current_user
from datetime import datetime

router = APIRouter(
    prefix="/activity_logs",
    tags=["activity_logs"]
)

@router.post("/", response_model=UserActivityLogOut, description="Add a new user activity record. Accepts action data and returns the created log.")
async def add_log(
    log: UserActivityLogCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    log_data = log.model_dump()
    log_data["user_id"] = current_user.id
    return await create_log(db, **log_data)

@router.get("/user/me", response_model=list[UserActivityLogOut], description="Get a list of all activity logs for the current user.")
async def logs_by_user(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await get_logs_by_user(db, current_user.id)

@router.get("/date_range/", response_model=list[UserActivityLogOut], description="Get a list of activity logs for the specified date range.")
async def logs_by_date_range(
    start: datetime, 
    end: datetime, 
    db: AsyncSession = Depends(get_db)
):
    return await get_logs_by_date_range(db, start, end)