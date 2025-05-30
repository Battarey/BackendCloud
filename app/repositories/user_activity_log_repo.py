from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_activity_log import UserActivityLog
from uuid import UUID
from datetime import datetime

# Creates a new user activity log entry
async def create_log(
    session: AsyncSession, 
    user_id: UUID, 
    action_type: str, 
    ip_address: str = None, 
    user_agent: str = None
):
    log = UserActivityLog(
        user_id=user_id,
        action_type=action_type,
        ip_address=ip_address,
        user_agent=user_agent
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log

# Gets all user activity logs by user ID
async def get_logs_by_user(
    session: AsyncSession,
    user_id: UUID
):
    result = await session.execute(
        select(UserActivityLog).where(UserActivityLog.user_id == user_id)
    )
    return result.scalars().all()

# Gets user activity logs for the specified date range
async def get_logs_by_date_range(
    session: AsyncSession, 
    start: datetime, 
    end: datetime
):
    result = await session.execute(
        select(UserActivityLog).where(UserActivityLog.action_time.between(start, end))
    )
    return result.scalars().all()