from fastapi import FastAPI
from app.routes.users import router as users_router
from app.routes.user_sessions import router as user_sessions_router
from app.routes.user_activity_logs import router as user_activity_logs_router
from app.routes.user_settings import router as user_settings_router
from app.routes.password_reset_tokens import router as password_reset_tokens_router
from app.routes.files import router as files_router
from app.routes.folders import router as folders_router
from contextlib import asynccontextmanager
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
import os
from app.middleware.logging_middleware import LoggingMiddleware
import logging

# Настройка базового логгера (если нужно)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check if the MinIO bucket exists and create it if not.
    try:
        # Use only asynchronous functions from minio_utils/minio_multipart
        pass
    except Exception as e:
        print(f"Error checking or creating MinIO bucket: {e}")
    # Инициализация FastAPI-Limiter
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, encoding="utf8", decode_responses=True)
    await FastAPILimiter.init(redis_client)
    yield

app = FastAPI(
    title="BattareyCloud API",
    description="Secure cloud storage API with FastAPI and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение middleware логирования
app.add_middleware(LoggingMiddleware)

app.include_router(users_router)
app.include_router(user_sessions_router)
app.include_router(user_activity_logs_router)
app.include_router(user_settings_router)
app.include_router(password_reset_tokens_router)
app.include_router(files_router)
app.include_router(folders_router)

@app.get("/")
async def root():
    return {"message": "Welcome to BattareyCloud API!"}