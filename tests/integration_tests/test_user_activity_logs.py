# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest
from datetime import datetime, timedelta, timezone
import uuid

@pytest.mark.asyncio
async def test_create_and_get_activity_log():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"loguser_{unique}",
        "email": f"loguser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create user

            # User registration
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"

            # User login
            user_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert user_resp.status_code == 200, f"Login failed: {user_resp.text}"
            user_id = user_resp.json()["user_id"]
            token = user_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create log (user_id убран, только action_type и др.)
            log_data = {
                "action_type": "login",
                "ip_address": "127.0.0.1",
                "user_agent": "pytest"
            }
            resp = await ac.post("/activity_logs/", json=log_data, headers=headers)
            assert resp.status_code == 200
            log = resp.json()
            assert log["user_id"] == user_id

            # Get user logs (убрать user_id из url, использовать /activity_logs/user/me)
            resp = await ac.get(f"/activity_logs/user/me", headers=headers)
            assert resp.status_code == 200
            logs = resp.json()
            assert any(l["id"] == log["id"] for l in logs)

            # Get logs by date range
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
            end = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
            resp = await ac.get(f"/activity_logs/date_range/?start={start}&end={end}")
            assert resp.status_code == 200