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
async def test_restore_physically_deleted_file(monkeypatch):
    async with app.router.lifespan_context(app):
        # Checks that restoring a file physically deleted from MinIO returns an error (404/400).
        # Mock file_repo.restore_file to emulate the absence of the file in MinIO
        from app.repositories import file_repo
        async def fake_restore_file(db, file_id):
            return None
        monkeypatch.setattr(file_repo, "restore_file", fake_restore_file)
        async with AsyncClient(app=app, base_url="http://test") as ac:
            user_data = {
                "username": "missingrestoreuser",
                "email": "missingrestoreuser@example.com",
                "password": "Test1234!"
            }
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            settings_data = {"storage_limit": 1024 * 1024, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=settings_data, headers=headers)
            # Uploading file
            files = {"file": ("missing.txt", b"missing", "text/plain")}
            upload_resp = await ac.post("/files/", files=files, headers=headers)
            assert upload_resp.status_code == 200
            file_id = upload_resp.json()["id"]
            # Delete file (to trash)
            del_resp = await ac.delete(f"/files/{file_id}", headers=headers)
            assert del_resp.status_code == 200
            # Trying to recover a file that is physically missing
            restore_resp = await ac.post(f"/files/restore/{file_id}", headers=headers)
            assert restore_resp.status_code in (400, 404), f"Restore of missing file should fail, got {restore_resp.status_code}"
