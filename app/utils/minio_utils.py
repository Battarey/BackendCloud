import os
from fastapi import HTTPException
from aiobotocore.session import get_session

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET = os.getenv("MINIO_BUCKET", "files")

# Loads bytes into MinIO by the specified object name and content type
async def upload_bytes_to_minio(
    object_name: str, 
    data: bytes, 
    content_type: str
) -> None:
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            await client.put_object(Bucket=BUCKET, Key=object_name, Body=data, ContentType=content_type)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO upload error: {e}")

# Gets object bytes from MinIO by object name
async def get_bytes_from_minio(
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
            response = await client.get_object(Bucket=BUCKET, Key=object_name)
            async with response['Body'] as stream:
                return await stream.read()
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found in storage: {e}")

# Removes an object from MinIO by object name
async def remove_object_from_minio(
    object_name: str
) -> None:
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            await client.delete_object(Bucket=BUCKET, Key=object_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO remove error: {e}")

# Generates a presigned URL to download an object from MinIO
async def get_presigned_url(
    minio_path, 
    expires_in=3600
):
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            url = await client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET, 'Key': minio_path},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO presigned url error: {e}")
