from dotenv import load_dotenv
import os

# Universal .env search: repository root, BackEnd, app
possible_envs = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"), # repository root
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),  # BackEnd
    os.path.join(os.path.dirname(__file__), ".env"),  # app
]
for dotenv_path in possible_envs:
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        break

from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/postgres")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    @property
    def effective_database_url(self) -> str:
        # If the environment variable TEST_USE_SQLITE=1 - use SQLite
        if os.getenv("TEST_USE_SQLITE") == "1":
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()