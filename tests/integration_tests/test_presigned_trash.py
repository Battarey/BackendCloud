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
async def test_presigned_url_for_file_in_trash():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"presignedtrashuser_{unique}",
        "email": f"presignedtrashuser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User registration
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            # Update settings if necessary
            settings_data = {"storage_limit": 1024 * 1024, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=settings_data, headers=headers)
            # Uploading file
            file_content = b"presigned trash test"
            files = {"file": ("trash_presigned.txt", file_content, "text/plain")}
            upload_resp = await ac.post("/files/", files=files, headers=headers)
            assert upload_resp.status_code == 200
            file_id = upload_resp.json()["id"]
            # Delete file (to trash)
            del_resp = await ac.delete(f"/files/{file_id}", headers=headers)
            assert del_resp.status_code == 200
            # Trying to get presigned URL
            presigned_resp = await ac.get(f"/files/presigned/{file_id}", headers=headers)
            assert presigned_resp.status_code in (400, 404), f"Presigned for trash file should fail, got {presigned_resp.status_code}"
