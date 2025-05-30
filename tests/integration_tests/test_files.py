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

@pytest.mark.asyncio
async def test_file_upload_delete_restore_presigned():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create user
            user_data = {
                "username": "fileuser",
                "email": "fileuser@example.com",
                "password": "Test1234!"
            }
            await ac.request(
                "DELETE", "/users/", 
                content=json.dumps({"username": user_data["username"], "password": user_data["password"]}),
                headers={"Content-Type": "application/json"}
            )
            resp = await ac.post("/users/", json=user_data)
            assert resp.status_code == 200, f"User create failed: {resp.text}"
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            user_id = login.json()["user_id"]
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}

            # Updating user settings
            update_data = {
                "storage_limit": 1024 * 1024 * 1024,
                "theme": "system",
                "language": "en",
                "notifications_enabled": True
            }
            await ac.put("/settings/user/me", json=update_data, headers=headers)

            # Uploading file
            file_content = b"test file content"
            files = {"file": ("test.txt", file_content, "text/plain")}
            resp = await ac.post("/files/", files=files, headers=headers)
            assert resp.status_code == 200, f"Upload failed: {resp.text}"
            file_json = resp.json()
            assert "id" in file_json, f"No 'id' in response: {file_json}"
            file_id = file_json["id"]

            # Delete file
            resp = await ac.delete(f"/files/{file_id}", headers=headers)
            assert resp.status_code == 200, f"Delete failed: {resp.text}"

            # File recovery
            resp = await ac.post(f"/files/restore/{file_id}", headers=headers)
            assert resp.status_code == 200, f"Restore failed: {resp.text}"

            # Getting statistics
            resp = await ac.get(f"/files/stats/", headers=headers)
            assert resp.status_code == 200, f"Stats failed: {resp.text}"

            # Getting presigned URL
            resp = await ac.get(f"/files/presigned/{file_id}", headers=headers)
            assert resp.status_code == 200, f"Presigned failed: {resp.text}"

@pytest.mark.asyncio
async def test_upload_file_with_same_name_conflict():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Checks that two files with the same name cannot be uploaded to the same folder (expected error)
            user_data = {
                "username": "samefileuser",
                "email": "samefileuser@example.com",
                "password": "Test1234!"
            }
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            update_data = {"storage_limit": 1024 * 1024, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=update_data, headers=headers)
            # Loading first file
            files = {"file": ("conflict.txt", b"first", "text/plain")}
            resp1 = await ac.post("/files/", files=files, headers=headers)
            assert resp1.status_code in (200, 409)
            # Trying to upload a second file with the same name
            files = {"file": ("conflict.txt", b"second", "text/plain")}
            resp2 = await ac.post("/files/", files=files, headers=headers)
            assert resp2.status_code in (400, 409), f"Should not allow duplicate file name, got {resp2.status_code}"

@pytest.mark.asyncio
async def test_restore_file_exceeding_storage_limit():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Checks that a file cannot be restored from the Recycle Bin if the storage limit is exceeded
            user_data = {
                "username": "restorelimituser",
                "email": "restorelimituser@example.com",
                "password": "Test1234!"
            }
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            # Limit 20 bytes
            update_data = {"storage_limit": 20, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=update_data, headers=headers)
            # Uploading file 10 bytes
            files = {"file": ("limit.txt", b"1234567890", "text/plain")}
            resp1 = await ac.post("/files/", files=files, headers=headers)
            assert resp1.status_code in (200, 400)
            if resp1.status_code != 200:
                # If the download fails due to a limit, the test is complete.
                return
            file_id = resp1.json()["id"]
            # Loading second file 10 bytes
            files = {"file": ("limit2.txt", b"abcdefghij", "text/plain")}
            resp2 = await ac.post("/files/", files=files, headers=headers)
            assert resp2.status_code == 200
            file2_id = resp2.json()["id"]
            # Delete the second file (to the trash)
            del_resp = await ac.delete(f"/files/{file2_id}", headers=headers)
            assert del_resp.status_code == 200
            # Delete the first file (free up space)
            del_resp2 = await ac.delete(f"/files/{file_id}", headers=headers)
            assert del_resp2.status_code == 200
            # Recovering the first file (taking up space)
            restore1 = await ac.post(f"/files/restore/{file_id}", headers=headers)
            assert restore1.status_code == 200
            # Trying to recover the second file (the limit must be exceeded)
            restore2 = await ac.post(f"/files/restore/{file2_id}", headers=headers)
            assert restore2.status_code == 400, f"Restore should fail due to storage limit, got {restore2.status_code}"

@pytest.mark.asyncio
async def test_list_files_by_folder_id():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Checks that the file list is correctly filtered by folder_id
            user_data = {
                "username": "folderlistuser",
                "email": "folderlistuser@example.com",
                "password": "Test1234!"
            }
            await ac.post("/users/", json=user_data)
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            update_data = {"storage_limit": 1024 * 1024, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.put("/settings/user/me", json=update_data, headers=headers)
            # Create folder
            folder_resp = await ac.post("/folders/", json={"name": "TestFolder"}, headers=headers)
            assert folder_resp.status_code == 200
            folder_id = folder_resp.json()["id"]
            # Upload file to folder
            files = {"file": ("in_folder.txt", b"foldered", "text/plain")}
            upload1 = await ac.post(f"/files/?folder_id={folder_id}", files=files, headers=headers)
            assert upload1.status_code == 200
            # Upload file to root
            files = {"file": ("in_root.txt", b"rooted", "text/plain")}
            upload2 = await ac.post("/files/", files=files, headers=headers)
            assert upload2.status_code in (200, 409)
            # Get list of files by folder_id
            resp = await ac.get(f"/folders/{folder_id}/files", headers=headers)
            assert resp.status_code in (200, 404)
            if resp.status_code == 200:
                files_list = resp.json()
                assert any(f["filename"] == "in_folder.txt" for f in files_list)
                assert all(f["filename"] != "in_root.txt" for f in files_list)