# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
import uuid
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_create_and_deactivate_session():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"sessionuser_{unique}",
        "email": f"sessionuser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create user for session
           
            # User registration
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"

            # User login
            user_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert user_resp.status_code == 200, f"Login failed: {user_resp.text}"
            user_id_str = user_resp.json()["user_id"] 
            headers = {"Authorization": f"Bearer {user_resp.json()['access_token']}"}

            # Create session (user_id убран, только device_info)
            session_data = {
                "device_info": {"os": "Windows", "browser": "Chrome"}
            }
            resp = await ac.post("/sessions/", json=session_data, headers=headers)
            assert resp.status_code == 200, f"Session creation failed: {resp.text}"
            session = resp.json()
            assert session["user_id"] == user_id_str 

            # Deactivate session
            resp = await ac.delete(f"/sessions/{session['token']}")
            assert resp.status_code == 200, f"Session deactivation failed: {resp.text}"