import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories import password_reset_token_repo
from app.schemas.password_reset_token import PasswordResetTokenCreate
from uuid import uuid4
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_create_and_validate_reset_token():
    db = AsyncMock()
    user_id = uuid4()
    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    token_data = PasswordResetTokenCreate(user_id=user_id, token=token, expires_at=expires_at)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    result = await password_reset_token_repo.create_reset_token(db, token_data.model_dump())
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
    assert result.user_id == user_id
    assert result.token == token
