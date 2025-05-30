from sqlalchemy import select, delete
from app.db.database import AsyncSessionLocal
from app.models.file import File as FileModel
from app.models.file_encryption import FileEncryption
from app.utils.minio_client import minio_client, BUCKET
from datetime import datetime, timezone, timedelta
import asyncio
from app.config import settings
from celery import Celery

celery_app = Celery(
    'tasks',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Empty the user's trash: removes files marked as deleted more than 24 hours ago
@celery_app.task
def cleanup_trash(
    user_id: str
):
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            expire_time = now - timedelta(hours=24)
            result = await db.execute(
                select(FileModel).where(
                    FileModel.is_deleted == True,
                    FileModel.deleted_at < expire_time,
                    FileModel.user_id == user_id
                )
            )
            files = result.scalars().all()
            for file in files:
                try:
                    minio_client.remove_object(BUCKET, file.path)
                except Exception:
                    pass # You can add logging of deletion errors from MinIO
                await db.execute(
                    delete(FileEncryption).where(FileEncryption.file_id == file.id)
                )
                await db.delete(file)
            await db.commit()
    asyncio.run(_cleanup())