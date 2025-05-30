# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest
from uuid import UUID
import uuid

@pytest.mark.asyncio
async def test_create_and_update_settings():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"settingsuser_{unique}",
        "email": f"settingsuser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:

            # User registration
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"
            
            # User login
            user_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert user_resp.status_code == 200, f"Login failed: {user_resp.text}"
            user_id = UUID(user_resp.json()["user_id"]) 
            headers = {"Authorization": f"Bearer {user_resp.json()['access_token']}"}

            # After registration, the settings are already created, we only do an update
            update_data = {
                "theme": "light"
            }
            resp = await ac.put(f"/settings/user/me", json=update_data, headers=headers)
            assert resp.status_code == 200, f"Update settings failed: {resp.text}"
            updated = resp.json()
            assert updated["theme"] == "light"