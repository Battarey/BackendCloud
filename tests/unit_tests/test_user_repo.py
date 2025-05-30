import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories import user_repo

@pytest.mark.asyncio
async def test_create_user():
    db = AsyncMock()
    username = "testuser"
    email = "test@example.com"
    password = "Test1234!"
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    result = await user_repo.create_user(db, username, email, password)
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
    assert result.username == username
    assert result.email == email
