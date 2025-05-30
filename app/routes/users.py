import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut, UserDelete
from app.repositories.user_repo import create_user, authenticate_user, delete_user, get_user_by_username
from app.repositories.user_settings_repo import create_settings
from app.schemas.user_settings import UserSettingsCreate
from app.core.security import create_access_token, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

ACCESS_TOKEN_EXPIRE_MINUTES = 60
TESTING = os.getenv("TESTING") == "1"

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserOut, description="Register a new user. Accepts username, email and password. Returns the created user's details.", dependencies=[Depends(RateLimiter(times=5, seconds=60))] if not TESTING else [])
async def register(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    db_user = await create_user(db, user.username, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="A user with that name or email already exists.")
    
    # Create default user settings
    settings_data = UserSettingsCreate(
        storage_limit=1024*1024*1024,  # 1GB
        theme="system",
        language="en",
        notifications_enabled=True
    ).model_dump()
    settings_data["user_id"] = db_user.id
    await create_settings(db, settings_data) 

    # Explicitly validate and return UserOut schema
    user_out = UserOut.model_validate(db_user)
    return user_out

# Additional route for registration with the same functionality
@router.post("/register", response_model=UserOut, description="Alternative registration endpoint for frontend compatibility.", dependencies=[Depends(RateLimiter(times=5, seconds=60))] if not TESTING else [])
async def register_alt(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    db_user = await create_user(db, user.username, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="A user with that name or email already exists.")
    
    # Create default user settings
    settings_data = UserSettingsCreate(
        storage_limit=1024*1024*1024,  # 1GB
        theme="system",
        language="en",
        notifications_enabled=True
    ).model_dump()
    settings_data["user_id"] = db_user.id
    await create_settings(db, settings_data) 

    # Explicitly validate and return UserOut schema
    user_out = UserOut.model_validate(db_user)
    return user_out

@router.get("/me", response_model=UserOut)
async def get_me(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not isinstance(current_user, UserOut):
        return UserOut.model_validate(current_user)
    return current_user

@router.get("/{username}", response_model=UserOut, description="Get user information by username. Returns user data if found.")
async def get_user(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    db_user = await get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    user_out = UserOut.model_validate(db_user)
    return user_out

@router.post("/login", description="User login by username and password. Returns access token, user ID, and username upon successful authentication.", dependencies=[Depends(RateLimiter(times=5, seconds=60))] if not TESTING else [])
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user_id": str(user.id)}

@router.delete("/", response_model=dict, description="Delete user. Requires username and password confirmation. Returns a message about successful deletion.")
async def remove_user(
    user: UserDelete, 
    db: AsyncSession = Depends(get_db)
):
    db_user = await authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect login or password")
    deleted = await delete_user(db, user.username)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User successfully deleted"}