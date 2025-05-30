# paths
import os
# app
from app.main import app
# other
from uuid import uuid4
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
def generate_token_data():
    return {
        "user_id": str(uuid4()),
        "token": str(uuid4()),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    }

@pytest.mark.asyncio
async def test_login_rate_limit():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            is_testing = os.getenv("TESTING") == "1"
            data = {"username": "testuser", "password": "wrongpass"}
            responses = []
            for _ in range(6):
                resp = await ac.post("/users/login", data=data)
                responses.append(resp)
            assert all(r.status_code in (401, 429) for r in responses)
            if is_testing:
                assert responses[-1].status_code == 401
            else:
                assert responses[-1].status_code == 429
                assert "Too Many Requests" in responses[-1].text

@pytest.mark.asyncio
async def test_reset_token_rate_limit():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            responses = []
            for _ in range(6):
                token_data = generate_token_data()
                resp = await ac.post("/reset_tokens/", json=token_data)
                responses.append(resp)
            # The first 5 can be 200 or 429 (if limit), 6th - 429
            assert all(r.status_code in (200, 429) for r in responses)
            assert responses[-1].status_code == 429
            assert "Too Many Requests" in responses[-1].text
