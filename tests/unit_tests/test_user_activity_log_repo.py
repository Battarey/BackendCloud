import pytest
from unittest.mock import AsyncMock, MagicMock
from app.repositories import user_activity_log_repo
from app.schemas.user_activity_log import UserActivityLogCreate
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_user_activity_log():
    db = AsyncMock()
    user_id = uuid4()
    log_data = UserActivityLogCreate(action_type="login", ip_address="127.0.0.1", user_agent="pytest")
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    result = await user_activity_log_repo.create_log(db, user_id, **log_data.model_dump())
    db.add.assert_called_once()
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
    assert result.user_id == user_id
    assert result.action_type == "login"
