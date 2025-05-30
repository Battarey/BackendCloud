import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories import folder_repo
from app.schemas.folder import FolderCreate
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_folder():
    db = AsyncMock()
    folder_data = FolderCreate(name="TestFolder", parent_id=None)
    user_id = uuid4()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    result = await folder_repo.create_folder(db, folder_data, user_id)
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
    assert result.name == "TestFolder"
    assert result.user_id == user_id
