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
async def test_delete_and_restore_file():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"trashuser_{unique}",
        "email": f"trashuser_{unique}@example.com",
        "password": "Test1234!"
    }

    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User registration
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"
            login_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
            login_data = login_resp.json()
            user_id = login_data["user_id"]
            token = login_data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}

            # Setup: File Upload
            file_content = b"content for trash test"
            files = {"file": ("trash_test.txt", file_content, "text/plain")}
            upload_resp = await ac.post(f"/files/", files=files, headers=headers)
            assert upload_resp.status_code in (200, 409), f"Upload failed: {upload_resp.text}"
            if upload_resp.status_code == 200:
                file_json = upload_resp.json()
                file_id = file_json["id"]
            else:
                # The file already exists, we are looking for its id by name
                files_list = await ac.get("/files/", headers=headers)
                file_id = next(f["id"] for f in files_list.json() if f["filename"] == "trash_test.txt")

            # Test: Delete File to Trash
            delete_resp = await ac.delete(f"/files/{file_id}", headers=headers)
            print('DELETE', delete_resp.json())
            assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
            assert delete_resp.json()["detail"] == "File moved to trash for 24h"

            # Check if the file is in the trash (optional, can be checked via GET /files/trash/)
            trash_resp = await ac.get(f"/files/trash/", headers=headers)
            print('TRASH', trash_resp.json())
            assert trash_resp.status_code == 200
            trash_files = trash_resp.json()
            assert any(f["id"] == file_id for f in trash_files), "File not found in trash"

            # Test: Restore File from Trash
            restore_resp = await ac.post(f"/files/restore/{file_id}", headers=headers)
            print('RESTORE', restore_resp.json())
            assert restore_resp.status_code == 200, f"Restore failed: {restore_resp.text}"
            restored_file = restore_resp.json()
            assert restored_file["id"] == file_id
            assert restored_file["is_deleted"] is False

            # Check that the file is restored (optional, can be checked via GET /files/)
            list_resp = await ac.get(f"/files/", headers=headers)
            print('LIST', list_resp.json())
            assert list_resp.status_code == 200
            active_files = list_resp.json()
            assert any(f["id"] == file_id for f in active_files), "File not found after restore"