from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.password_utils import hash_password, verify_password
from uuid import UUID

# Creates a new user with the specified username, email and password
async def create_user(
    session: AsyncSession,
    username: str, 
    email: str, 
    password: str
):
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),   
    )
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        return None

# Gets user by username
async def get_user_by_username(
    session: AsyncSession, 
    username: str
):
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

# Gets a user by their ID
async def get_user_by_id(
    session: AsyncSession,
    user_id: UUID
):
    try:
        uid = UUID(str(user_id))
    except Exception as e:
        print(f"[get_user_by_id] Invalid user_id: {user_id}, error: {e}")
        return None
    print(f"[get_user_by_id] Searching for user_id: {uid} (type: {type(uid)})")
    result = await session.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    print(f"[get_user_by_id] Found: {user}")
    return user

# Authenticates the user by username and password
async def authenticate_user(
    session: AsyncSession, 
    username: str, 
    password: str
):
    user = await get_user_by_username(session, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None

# Deletes user by username
async def delete_user(
    session: AsyncSession, 
    username: str
):
    user = await get_user_by_username(session, username)
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False