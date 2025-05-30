# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_trash_file_expiry_and_deletion():
    user_data = {
        "username": "trashyuser",
        "email": "trashyuser@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            settings_data = {"storage_limit": 1024 * 1024, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=settings_data, headers=headers)
            # Uploading file
            files = {"file": ("expire.txt", b"expireme", "text/plain")}
            upload_resp = await ac.post("/files/", files=files, headers=headers)
            assert upload_resp.status_code == 200
            file_id = upload_resp.json()["id"]
            # Delete file (to trash)
            del_resp = await ac.delete(f"/files/{file_id}", headers=headers)
            assert del_resp.status_code == 200
            # Emulate expiration of storage time (call celery task directly via API or wait if there is an endpoint)
            # This assumes that there is an endpoint /files/cleanup_trash for tests
            cleanup = await ac.post("/files/cleanup_trash", headers=headers)
            assert cleanup.status_code == 202
            # Check that the file no longer exists
            get_resp = await ac.get(f"/files/{file_id}", headers=headers)
            assert get_resp.status_code == 404, f"File should be deleted from trash, got {get_resp.status_code}"
