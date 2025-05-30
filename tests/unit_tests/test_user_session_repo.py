import pytest
from unittest.mock import AsyncMock
from app.repositories import user_session_repo
from app.models.user_session import UserSession
from uuid import uuid4

@pytest.mark.asyncio
async def test_deactivate_session():
    session = AsyncMock()
    token = "testtoken"
    user_session = UserSession(id=uuid4(), user_id=uuid4(), token=token, is_active=True)
    user_session_repo.get_session_by_token = AsyncMock(return_value=user_session)
    session.commit = AsyncMock()
    result = await user_session_repo.deactivate_session(session, token)
    assert result is True
    assert user_session.is_active is False
    session.commit.assert_awaited()
