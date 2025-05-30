import redis.asyncio as redis
import json
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

UPLOAD_EXPIRATION_SECONDS = 60 * 60 * 24 # 24 hours

# Stores information about the multipart load in Redis
async def store_upload_info(
    upload_id: str, 
    object_name: str,
    user_id: str
):
    key = f"upload:{upload_id}"
    data = json.dumps({"object_name": object_name, "user_id": user_id})
    await redis_client.setex(key, UPLOAD_EXPIRATION_SECONDS, data)

# Gets information about a multipart load from Redis
async def get_upload_info(
    upload_id: str
) -> dict | None:
    key = f"upload:{upload_id}"
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

# Removes multipart load information from Redis
async def delete_upload_info(
    upload_id: str
):
    key = f"upload:{upload_id}"
    await redis_client.delete(key)
