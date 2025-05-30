import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories import file_repo
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_file():
    db = AsyncMock()
    user_id = uuid4()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    result = await file_repo.create_file(
        db,
        filename="test.txt",
        user_id=user_id,
        size=10,
        content_type="text/plain",
        path="test/path.txt",
        folder_id=None
    )
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
    assert result.filename == "test.txt"
    assert result.user_id == user_id
