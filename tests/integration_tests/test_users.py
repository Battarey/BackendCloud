# paths
import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_register_and_login():
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/users/", json=user_data)
            assert response.status_code in (200, 400)
            if response.status_code == 200:
                data = response.json()
                assert data["username"] == user_data["username"]
            response = await ac.post("/users/login", data={
                "username": "testuser",
                "password": "Test1234!"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            assert "access_token" in data
            assert "user_id" in data
