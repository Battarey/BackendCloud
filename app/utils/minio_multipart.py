from aiobotocore.session import get_session
import os
from fastapi import HTTPException
from typing import List

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "files")

# Initiates a multipart upload of an object to MinIO and returns the upload_id
async def initiate_multipart_upload(
    object_name: str
) -> str:
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            response = await client.create_multipart_upload(Bucket=MINIO_BUCKET, Key=object_name)
            return response['UploadId']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initiate multipart upload: {e}")

# Uploads a portion of a file as part of a multipart upload
async def upload_part(
    object_name: str,
    upload_id: str, 
    part_number: int, 
    data: bytes
) -> str:
    session = get_session()
    async with session.create_client(
        's3',
        endpoint_url=f"http://{MINIO_ENDPOINT}",
        aws_secret_access_key=MINIO_SECRET_KEY,
        aws_access_key_id=MINIO_ACCESS_KEY,
        region_name='us-east-1',
    ) as client:
        try:
            response = await client.upload_part(
                Bucket=MINIO_BUCKET,
                Key=object_name,
                UploadId=upload_id,
                PartNumber=part_number,
                Body=data
            )
            return response['ETag']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload part {part_number}: {e}")

# Completes a multipart upload by merging all parts into a single object
async def complete_multipart_upload(
    object_name: str, 
    upload_id: str, 
    parts: List[dict]
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
            parts_list = [{"ETag": p['etag'], "PartNumber": p['part_number']} for p in parts]
            await client.complete_multipart_upload(
                Bucket=MINIO_BUCKET,
                Key=object_name,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts_list}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to complete multipart upload: {e}")

# Aborts (cancels) a multipart object download
async def abort_multipart_upload(
    object_name: str, 
    upload_id: str
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
            await client.abort_multipart_upload(Bucket=MINIO_BUCKET, Key=object_name, UploadId=upload_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to abort multipart upload: {e}")

# Gets object metadata from MinIO (analogous to stat)
async def stat_object(
    object_name: str
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
            return await client.head_object(Bucket=MINIO_BUCKET, Key=object_name)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Object not found: {e}")
