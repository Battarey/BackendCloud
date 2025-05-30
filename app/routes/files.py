# fastapi
from fastapi.responses import Response
from fastapi import APIRouter, UploadFile, File as FastAPIFile, Depends, HTTPException, Query
# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
# app
from app.db.database import get_db
from app.schemas.file import FileOut
from app.repositories import file_repo
from app.repositories.user_settings_repo import get_settings_by_user
from app.schemas import file as file_schema
from app.core.security import get_current_user
from app.models.user import User
from app.utils.antivirus import scan_bytes_for_viruses
from app.core.encryption import encrypt_file
from app.utils.minio_utils import upload_bytes_to_minio
from app.models.file_encryption import FileEncryption
# tasks
from tasks.cleanup import cleanup_trash
# other
from uuid import UUID
from typing import List, Optional
import logging

router = APIRouter(
    prefix="/files", 
    tags=["files"]
)

logger = logging.getLogger(__name__)

@router.post("/", response_model=FileOut, description="Upload a file, checks storage limit and viruses.")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    settings = await get_settings_by_user(db, user_id)
    if not settings:
        raise HTTPException(status_code=400, detail="User settings not found")
    storage_limit = settings.storage_limit
    used_size = await file_repo.get_user_storage_usage(db, user_id)
    content = await file.read()
    if used_size + len(content) > storage_limit:
        raise HTTPException(status_code=400, detail="Storage limit exceeded")

    # Check: a file with this name already exists in this folder (and has not been deleted)
    existing_file = await file_repo.get_file_by_name_and_folder(db, file.filename, user_id, folder_id)
    if existing_file:
        raise HTTPException(status_code=409, detail="File with this name already exists in the folder")

    # 1. Virus check
    await scan_bytes_for_viruses(content)

    # 2. Encrypting a file (using user_id as password)
    encrypted_data, salt, iv = encrypt_file(content, str(user_id))

    # 3. Generating a path for MinIO
    minio_path = f"{user_id}/{folder_id or 'root'}/{file.filename}"

    # 4. Loading into MinIO
    await upload_bytes_to_minio(minio_path, encrypted_data, file.content_type)

    # 5. Saving a file record to the database
    db_file = await file_repo.create_file(
        db,
        filename=file.filename,
        user_id=user_id,
        size=len(content),
        content_type=file.content_type,
        path=minio_path,
        folder_id=folder_id
    )
    # 6. Save salt and iv to file
    db.add(FileEncryption(
        file_id=db_file.id,
        encryption_salt=salt,
        encryption_iv=iv
    ))
    await db.commit()
    await db.refresh(db_file)
    return db_file

@router.get("/", response_model=List[FileOut], description="List all files for the current user.")
async def list_files(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await file_repo.get_files_by_user(db, current_user.id)

@router.put("/{file_id}/move", response_model=dict, description="Move file to another folder.")
async def move_file_route(
    file_id: UUID,
    new_folder_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    await file_repo.move_file(db, file_id, new_folder_id)
    return {"detail": "File moved"}

@router.get("/{file_id}", response_model=FileOut, description="Get information about a file by its ID. Not available for files in the Recycle Bin.")
async def get_file_info(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    file = await file_repo.get_file_info(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.get("/download/{file_id}", description="Download file by ID. Not available for files from the basket.")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    file = await file_repo.download_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.options("/download/{file_id}", description="CORS preflight for file download.")
def options_download_file(
    file_id: UUID
):
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "http://localhost:3500",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    })

@router.delete("/{file_id}", response_model=dict, description="Delete file (move to trash). The file will be stored in the trash for 24 hours before being permanently deleted.")
async def delete_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await file_repo.delete_file(db, file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return {"detail": "File moved to trash for 24h"}

@router.post("/restore/{file_id}", response_model=FileOut, description="Restore file from Recycle Bin. If storage limit is exceeded, recovery is impossible.")
async def restore_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    file = await file_repo.restore_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.get("/presigned/{file_id}", response_model=dict, description="Get a temporary (presigned) link to download a file from MinIO. Not available for files from the Recycle Bin.")
async def get_presigned_url(
    file_id: UUID,
    expires_in: int = 3600,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await file_repo.get_presigned_url(db, file_id, expires_in)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found or is deleted")

@router.get("/search/", response_model=List[FileOut], description="Search files by name for the current user.")
async def search_files(
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await file_repo.search_files(db, current_user.id, filename=filename, content_type=content_type)

@router.get("/trash/", response_model=List[FileOut], description="Get all files in trash for the current user.")
async def get_trash_files(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await file_repo.get_trash_files(db, current_user.id)

@router.get("/stats/", response_model=dict, description="Get file statistics for the current user.")
async def get_file_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await file_repo.get_file_stats_by_user(db, current_user.id)

@router.get("/{file_id}/preview", description="Get a preview of the file by its ID.")
async def preview_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    file = await file_repo.preview_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.post("/initiate_upload", response_model=file_schema.InitiateUploadResponse, description="Initiate a multipart upload.")
async def initiate_upload(
    request_data: file_schema.InitiateUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await file_repo.initiate_upload(db, current_user.id, request_data)

@router.post("/upload_chunk", description="Upload a chunk for multipart upload.")
async def upload_chunk(
    upload_id: str = Query(...),
    part_number: int = Query(...),
    file_chunk: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await file_repo.upload_chunk(db, current_user.id, upload_id, part_number, file_chunk)

@router.post("/complete_upload", response_model=file_schema.FileOut, description="Complete a multipart upload.")
async def complete_upload(
    completion_data: file_schema.CompleteUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await file_repo.complete_upload(db, current_user.id, completion_data)

@router.delete("/abort_upload/{upload_id}", status_code=204, description="Abort a multipart upload.")
async def abort_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user)
):
    await file_repo.abort_upload(current_user.id, upload_id)
    return Response(status_code=204)

@router.post("/cleanup_trash", status_code=202)
async def cleanup_user_trash(current_user: User = Depends(get_current_user)):
    # Run celery task only for current user
    cleanup_trash.delay(str(current_user.id))
    return {"detail": "Cleanup started"}
