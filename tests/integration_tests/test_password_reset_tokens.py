# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest
import json
from uuid import uuid4
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
async def test_create_and_use_reset_token():
    user_data = {
        "username": "resetuser",
        "email": "resetuser@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create user
            await ac.request("DELETE", "/users/", content=json.dumps({"username": user_data["username"], "password": user_data["password"]}), headers={"Content-Type": "application/json"})
            await ac.post("/users/", json=user_data)
            user_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert user_resp.status_code == 200, f"Login failed: {user_resp.text}"
            user_id = user_resp.json()["user_id"]

            # Create a reset token
            token_data = {
                "user_id": user_id,
                "token": str(uuid4()),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            }
            resp = await ac.post("/reset_tokens/", json=token_data)
            assert resp.status_code == 200
            token = resp.json()
            assert token["user_id"] == user_id

            # Check token validity
            resp = await ac.get(f"/reset_tokens/{token['token']}/valid")
            assert resp.status_code == 200

            # Use token
            resp = await ac.post(f"/reset_tokens/{token['token']}/use")
            assert resp.status_code == 200
            used = resp.json()
            assert used["is_used"] is True