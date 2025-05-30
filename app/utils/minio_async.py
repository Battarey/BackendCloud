from aiobotocore.session import get_session
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "files")

# Asynchronously get an object from MinIO by bucket and object name
async def get_object_async(
    bucket: str, 
    object_name: str
) -> bytes:
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            response = await client.get_object(Bucket=bucket, Key=object_name)
            async with response['Body'] as stream:
                data = await stream.read()
            return data
        except Exception as e:
            raise Exception(f"Failed to get object {object_name} from MinIO: {e}")
