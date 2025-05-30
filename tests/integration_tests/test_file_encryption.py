# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest
import uuid

@pytest.mark.asyncio
async def test_file_encryption_and_decryption():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"cryptouser_{unique}",
        "email": f"cryptouser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            # Settings are already created during registration, no need to recreate them
            # File upload
            filename = f"crypto_{uuid.uuid4().hex}.txt"
            original_content = b"encryption test content"
            files = {"file": (filename, original_content, "text/plain")}
            upload_resp = await ac.post("/files/", files=files, headers=headers)
            assert upload_resp.status_code == 200
            file_id = upload_resp.json()["id"]
            # Downloading file
            download_resp = await ac.get(f"/files/download/{file_id}", headers=headers)
            assert download_resp.status_code == 200
            assert download_resp.content == original_content, "Downloaded file content does not match uploaded (encryption/decryption failed)"
