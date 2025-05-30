# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
# app
from app.models.folder import Folder
from app.schemas.folder import FolderCreate
from app.models.file import File
# other
from uuid import UUID
from typing import Optional

# Creates a new folder for the user
async def create_folder(
    db: AsyncSession, 
    folder: FolderCreate, 
    user_id: UUID
):
    db_folder = Folder(
        name=folder.name,
        parent_id=folder.parent_id,
        user_id=user_id
    )
    db.add(db_folder)
    await db.commit()
    await db.refresh(db_folder)
    return db_folder

# Gets a folder by its ID
async def get_folder(
    db: AsyncSession, 
    folder_id: UUID
):
    result = await db.execute(select(Folder).where(Folder.id == folder_id))
    return result.scalar_one_or_none()

# Gets all user folders
async def get_folders_by_user(
    db: AsyncSession,
    user_id: UUID
):
    result = await db.execute(select(Folder).where(Folder.user_id == user_id))
    return result.scalars().all()

# Gets all user folders with the specified parent
async def get_folders_by_parent(
    db: AsyncSession, 
    user_id: UUID, 
    parent_id: Optional[UUID] = None
):
    result = await db.execute(
        select(Folder).where(Folder.user_id == user_id, Folder.parent_id == parent_id)
    )
    return result.scalars().all()

# Deletes a folder by its ID
async def delete_folder(
    db: AsyncSession, 
    folder_id: UUID
):
    await db.execute(delete(Folder).where(Folder.id == folder_id))
    await db.commit()

# Recursively deletes a folder, all subfolders and files
async def delete_folder_recursive(
    db: AsyncSession, 
    folder_id: UUID
):
    # Delete all nested folders recursively
    subfolders = await db.execute(select(Folder).where(Folder.parent_id == folder_id))
    for subfolder in subfolders.scalars().all():
        await delete_folder_recursive(db, subfolder.id)
    # Delete all files in the folder
    await db.execute(delete(File).where(File.folder_id == folder_id))
    # Delete the folder itself
    await db.execute(delete(Folder).where(Folder.id == folder_id))
    await db.commit()

# Moves a folder to another parent folder
async def move_folder(
    db: AsyncSession, 
    folder_id: UUID, 
    new_parent_id: UUID
):
    await db.execute(
        update(Folder)
        .where(Folder.id == folder_id)
        .values(parent_id=new_parent_id)
    )
    await db.commit()

# Renames the folder
async def rename_folder(
    db: AsyncSession, 
    folder_id: UUID, 
    new_name: str
):
    await db.execute(
        update(Folder)
        .where(Folder.id == folder_id)
        .values(name=new_name)
    )
    await db.commit()