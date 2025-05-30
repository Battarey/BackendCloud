from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.folder import FolderCreate, FolderOut
from app.repositories.folder_repo import create_folder, get_folder, get_folders_by_user, get_folders_by_parent, delete_folder, delete_folder_recursive, rename_folder, move_folder
from app.core.security import get_current_user
from uuid import UUID
from typing import List, Optional

router = APIRouter(
    prefix="/folders",
    tags=["folders"]
)

@router.post("/", response_model=FolderOut, description="Create folder")
async def create(
    folder: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await create_folder(db, folder, current_user.id)

@router.get("/{folder_id}", response_model=FolderOut, description="Get folder by id")
async def get(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    folder = await get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return folder

@router.get("/", response_model=List[FolderOut], description="List all folders for the current user.")
async def list_folders(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await get_folders_by_user(db, current_user.id)

@router.get("/by_parent/", response_model=List[FolderOut], description="List folders by parent folder for the current user.")
async def list_by_parent(
    parent_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await get_folders_by_parent(db, current_user.id, parent_id)

@router.delete("/{folder_id}", description="Delete folder by id")
async def delete(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    folder = await get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await delete_folder(db, folder_id)
    return {"detail": "Folder deleted"}

@router.delete("/{folder_id}/recursive", description="Recursively delete folder and all contents")
async def delete_recursive(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    folder = await get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await delete_folder_recursive(db, folder_id)
    return {"detail": "Folder and all contents deleted"}

@router.put("/{folder_id}/rename", description="Rename folder")
async def rename(
    folder_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    folder = await get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await rename_folder(db, folder_id, data["new_name"])
    return {"detail": "Folder renamed"}

@router.put("/{folder_id}/move", description="Move folder to another parent")
async def move(
    folder_id: UUID,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    folder = await get_folder(db, folder_id)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    if folder.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await move_folder(db, folder_id, data["new_parent_id"])
    return {"detail": "Folder moved"}