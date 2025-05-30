from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
from app.models.file import File
from app.models.file_encryption import FileEncryption
from uuid import UUID
from typing import Optional, List
from app.utils.minio_utils import get_presigned_url as minio_get_presigned_url, get_bytes_from_minio
from app.utils.minio_multipart import initiate_multipart_upload, upload_part, complete_multipart_upload, stat_object
from datetime import datetime, timezone
from fastapi.responses import Response
from app.core.encryption import decrypt_file

UPLOADS = {}

# Creates a record about the file in the database
async def create_file(
    db: AsyncSession,
    filename: str,
    user_id: UUID,
    size: int,
    content_type: str,
    path: str,
    folder_id: Optional[UUID] = None
):
    db_file = File(
        filename=filename,
        user_id=user_id,
        size=size,
        content_type=content_type,
        path=path,
        folder_id=folder_id
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file

# Gets a file by its ID
async def get_file(
    db: AsyncSession,
    file_id: UUID
) -> Optional[File]:
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()

# Gets information about a file if it is not deleted
async def get_file_info(db: AsyncSession, file_id: UUID):
    from app.models.file import File
    result = await db.execute(select(File).where(File.id == file_id, File.is_deleted == False))
    return result.scalar_one_or_none()

# Gets a list of files in the user's folder
async def get_files_by_folder(
    db: AsyncSession,
    user_id: UUID,
    folder_id: Optional[UUID] = None
) -> List[File]:
    result = await db.execute(
        select(File).where(File.user_id == user_id, File.folder_id == folder_id)
    )
    return result.scalars().all()

# Gets all user files (not deleted)
async def get_files_by_user(
    db: AsyncSession, 
    user_id: UUID
):
    result = await db.execute(
        select(File).where(File.user_id == user_id, File.is_deleted == False)
    )
    return result.scalars().all()

# Marks a file as deleted (is_deleted=True)
async def delete_file(
    db: AsyncSession,
    file_id: UUID
):
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise Exception("File not found")
    file.is_deleted = True
    file.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return file

# Moves a file to another folder
async def move_file(
    db: AsyncSession, 
    file_id: UUID, 
    new_folder_id: Optional[UUID]
):
    await db.execute(
        update(File)
        .where(File.id == file_id)
        .values(folder_id=new_folder_id)
    )
    await db.commit()

# Gets the total amount of space occupied by the user
async def get_user_storage_usage(
    db: AsyncSession, 
    user_id: UUID
):
    result = await db.execute(
        select(func.coalesce(func.sum(File.size), 0)).where(File.user_id == user_id, File.is_deleted == False)
    )
    return result.scalar_one()

# Restores a file from the Recycle Bin if there is enough space
async def restore_file(
    db: AsyncSession, 
    file_id: UUID
):
    # Find file
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise Exception("File not found")
    if not file.is_deleted:
        return file  # Already restored
    # Check storage limit
    from app.repositories.user_settings_repo import get_settings_by_user
    settings = await get_settings_by_user(db, file.user_id)
    if not settings:
        raise Exception("User settings not found")
    used_size = await get_user_storage_usage(db, file.user_id)
    if used_size + file.size > settings.storage_limit:
        raise Exception("Storage limit exceeded, cannot restore file")
    file.is_deleted = False
    file.deleted_at = None
    await db.commit()
    await db.refresh(file)
    return file

# Gets user statistics: number of files, total size, top 10 files by size
async def get_file_stats(
    db: AsyncSession, 
    user_id: UUID
):
    # Total files and total size
    result = await db.execute(
        select(func.count(File.id), func.coalesce(func.sum(File.size), 0))
        .where(File.user_id == user_id, File.is_deleted == False)
    )
    total_files, total_size = result.one()
    # Top 10 files by size
    result = await db.execute(
        select(File.id, File.filename, File.size)
        .where(File.user_id == user_id, File.is_deleted == False)
        .order_by(File.size.desc())
        .limit(10)
    )
    top_files = [
        {"id": str(row.id), "filename": row.filename, "size": row.size}
        for row in result.fetchall()
    ]
    return {
        "total_files": total_files,
        "total_size": total_size,
        "top_files": top_files
    }
get_file_stats_by_user = get_file_stats

# Gets a presigned URL to download a file from MinIO
async def get_presigned_url(
    db: AsyncSession, 
    file_id: UUID, 
    expires_in: int = 3600
):
    result = await db.execute(select(File).where(File.id == file_id, File.is_deleted == False))
    file = result.scalar_one_or_none()
    if not file:
        raise Exception("File not found or is deleted")
    url = await minio_get_presigned_url(file.path, expires_in)
    return {"url": url}

# Gets a list of the user's files in the trash
async def get_trash_files(
    db: AsyncSession, 
    user_id: UUID
):
    result = await db.execute(
        select(File).where(File.user_id == user_id, File.is_deleted == True)
    )
    return result.scalars().all()

# Search files by name and/or content type
async def search_files(
    db: AsyncSession, 
    user_id: UUID, 
    filename: Optional[str] = None, 
    content_type: Optional[str] = None, 
    limit: int = 20, 
    offset: int = 0
):
    query = select(File).where(File.user_id == user_id, File.is_deleted == False)
    if filename:
        query = query.where(File.filename.ilike(f"%{filename}%"))
    if content_type:
        query = query.where(File.content_type == content_type)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

# Initiates a multipart file download (MinIO)
async def initiate_upload(
    db,
    user_id, 
    request_data
):
    object_name = f"{user_id}/uploads/{request_data.filename}"
    upload_id = await initiate_multipart_upload(object_name)
    UPLOADS[upload_id] = object_name
    return {"upload_id": upload_id, "object_name": object_name}

# Uploads a portion of a file as part of a multipart upload
async def upload_chunk(
    db,
    user_id, 
    upload_id, 
    part_number, 
    file_chunk
):
    object_name = UPLOADS.get(upload_id)
    if not object_name:
        raise Exception("Upload session not found")
    data = await file_chunk.read()
    etag = await upload_part(object_name, upload_id, part_number, data)
    return {"etag": etag}

# Completes the multipart download and creates a file entry
async def complete_upload(
    db, 
    user_id, 
    completion_data
):
    await complete_multipart_upload(
        completion_data.object_name,
        completion_data.upload_id,
        [part.model_dump() for part in completion_data.parts]
    )
    filename = getattr(completion_data, "file_name", None) or completion_data.object_name.split("/")[-1]
    content_type = getattr(completion_data, "content_type", "application/octet-stream")
    stat = await stat_object(completion_data.object_name)
    size = stat["ContentLength"] if "ContentLength" in stat else 0
    return await create_file(
        db,
        filename=filename,
        user_id=user_id,
        size=size,
        content_type=content_type,
        path=completion_data.object_name,
        folder_id=None
    )

# Downloads and decrypts the file, returns as an HTTP response
async def download_file(db: AsyncSession, file_id: UUID):
    result = await db.execute(select(File).where(File.id == file_id, File.is_deleted == False))
    file = result.scalar_one_or_none()
    if not file:
        raise Exception("File not found")
    data = await get_bytes_from_minio(file.path)
    # Получаем salt и iv из file_encryption
    result_enc = await db.execute(select(FileEncryption).where(FileEncryption.file_id == file.id))
    file_enc = result_enc.scalar_one_or_none()
    if not file_enc:
        raise Exception("Encryption params not found")
    salt = file_enc.encryption_salt
    iv = file_enc.encryption_iv
    decrypted = decrypt_file(data, str(file.user_id), salt=salt, iv=iv)
    return Response(
        content=decrypted,
        media_type=file.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={file.filename}"
        }
    )

# Gets a file by name and folder
async def get_file_by_name_and_folder(db, filename, user_id, folder_id):
    from app.models.file import File
    stmt = select(File).where(
        File.user_id == user_id,
        File.filename == filename,
        File.folder_id == folder_id,
        File.is_deleted == False
    )
    result = await db.execute(stmt)
    return result.scalars().first()