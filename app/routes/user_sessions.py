from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user_session import UserSessionCreate, UserSessionOut
from app.repositories.user_session_repo import create_session, get_active_sessions_by_user, deactivate_session
from app.core.security import get_current_user

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"]
)

@router.post("/", response_model=UserSessionOut, description="Create a new user session. Accepts device information, returns session data.")
async def create_user_session(
    session_data: UserSessionCreate, 
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_session = await create_session(
        db,
        user_id=current_user.id,
        device_info=session_data.device_info
    )
    return user_session

@router.get("/user/me", response_model=list[UserSessionOut], description="Get a list of active sessions for the current user.")
async def get_user_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    sessions = await get_active_sessions_by_user(db, current_user.id)
    return sessions

@router.delete("/{token}", response_model=dict, description="End (deactivate) a session using its token. Returns a message about successful completion.")
async def logout(
    token: str, 
    db: AsyncSession = Depends(get_db)
):
    result = await deactivate_session(db, token)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found or already inactive")
    return {"detail": "Session ended"}