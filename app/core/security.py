# fastapi
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
# app
from app.db.database import get_db
from app.models.user import User
# other
from jose import jwt, JWTError
from datetime import datetime, timedelta
from uuid import UUID
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "test_secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days by default
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Hashes the user's password using bcrypt
def hash_password(
    password: str
) -> str:
    return pwd_context.hash(password)

# Checks if a password matches a hash using bcrypt
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Creates a JWT access token with a specified lifetime
def create_access_token(
    data: dict,
    expires_delta: timedelta = None
):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Gets the current user by JWT token from the request
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        try:
            user_id = UUID(user_id)
        except Exception as e:
            print(f"[get_current_user] Invalid user_id in token: {user_id}, error: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    from app.repositories.user_repo import get_user_by_id
    user = await get_user_by_id(db, user_id)
    if not user:
        print(f"[get_current_user] User not found by id: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    return user