from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
