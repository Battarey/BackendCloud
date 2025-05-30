# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.main import app
# other
from httpx import AsyncClient
import pytest
from uuid import uuid4
import uuid

@pytest.mark.asyncio
async def test_chunked_upload():
    unique = uuid.uuid4().hex[:8]
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # User registration
            user_data = {
                "username": f"chunkuser_{unique}",
                "email": f"chunkuser_{unique}@example.com",
                "password": "Test1234!"
            }
            resp = await ac.post("/users/", json=user_data)
            assert resp.status_code == 200, f"User create failed: {resp.text}"
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            user_id = login.json()["user_id"]
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # Initialize multipart upload
            file_name = f"chunked_test_{uuid4().hex[:8]}.txt"
            # S3/MinIO: minimum size of part (except the last one) — 5 MB
            min_part_size = 5 * 1024 * 1024
            total_content = b"A" * min_part_size + b"B" * 1024  # 5 MB + 1 KB
            chunk1 = total_content[:min_part_size]
            chunk2 = total_content[min_part_size:]
            expected_size = len(total_content)
            init_data = {
                "filename": file_name,
                "size": expected_size,
                "content_type": "text/plain"
            }
            resp = await ac.post("/files/initiate_upload", json=init_data, headers=headers)
            assert resp.status_code == 200, f"Initiate upload failed: {resp.text}"
            upload_id = resp.json()["upload_id"]
            object_name = resp.json()["object_name"]

            # Loading chunks
            etags = []
            for i, chunk in enumerate([chunk1, chunk2], start=1):
                files = {"file_chunk": (file_name, chunk, "text/plain")}
                params = {"upload_id": upload_id, "part_number": i}
                resp = await ac.post("/files/upload_chunk", params=params, files=files, headers=headers)
                assert resp.status_code == 200, f"Upload chunk {i} failed: {resp.text}"
                etag = resp.json().get("etag")
                assert etag, f"No ETag returned for chunk {i}"
                etags.append({"part_number": i, "etag": etag})

            # Download complete
            complete_data = {
                "upload_id": upload_id,
                "object_name": object_name,
                "parts": etags,
                "file_name": file_name,
                "content_type": "text/plain"
            }
            resp = await ac.post("/files/complete_upload", json=complete_data, headers=headers)
            assert resp.status_code == 200, f"Complete upload failed: {resp.text}"
            file_id = resp.json()["id"]
            assert resp.json()["filename"] == file_name

            # Check that the file has appeared for the user
            resp = await ac.get(f"/files/?user_id={user_id}", headers=headers)
            assert resp.status_code == 200, f"Get files failed: {resp.text}"
            files_list = resp.json()
            assert any(f["id"] == file_id for f in files_list), "Uploaded file not found in user files"
