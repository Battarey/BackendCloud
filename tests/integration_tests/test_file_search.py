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
async def test_search_file_by_name_and_type():
    unique = uuid.uuid4().hex[:8]
    user_data = {
        "username": f"searchuser_{unique}",
        "email": f"searchuser_{unique}@example.com",
        "password": "Test1234!"
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Register user
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"Registration failed: {resp_reg.text}"

            # Login user
            login_resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
            login_data = login_resp.json()
            user_id = login_data["user_id"]
            token = login_data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}

            # Setup: File Uploads 
            # File 1: Specific name
            unique_filename = f"unique_search_test_{uuid4()}.txt"
            file_content_1 = b"content for name search"
            files_1 = {"file": (unique_filename, file_content_1, "text/plain")}
            upload_resp_1 = await ac.post(f"/files/", files=files_1, headers=headers)
            assert upload_resp_1.status_code == 200, f"Upload 1 failed: {upload_resp_1.text}"
            file_id_1 = upload_resp_1.json()["id"]

            # File 2: Specific content type (PDF)
            pdf_filename = f"search_test_{uuid4()}.pdf"
            file_content_2 = b"%PDF-1.4 test pdf content"
            files_2 = {"file": (pdf_filename, file_content_2, "application/pdf")}
            upload_resp_2 = await ac.post(f"/files/", files=files_2, headers=headers)
            assert upload_resp_2.status_code == 200, f"Upload 2 failed: {upload_resp_2.text}"
            file_id_2 = upload_resp_2.json()["id"]

            # Test: Search by Name 
            search_name_resp = await ac.get(f"/files/search/?filename=unique_search_test", headers=headers)
            assert search_name_resp.status_code == 200, f"Search by name failed: {search_name_resp.text}"
            search_results_name = search_name_resp.json()
            assert any(f["filename"] == unique_filename for f in search_results_name), "File not found by name search"
            assert len(search_results_name) >= 1

            # Test: Search by Content Type 
            search_type_resp = await ac.get(f"/files/search/?content_type=application/pdf", headers=headers)
            assert search_type_resp.status_code == 200, f"Search by type failed: {search_type_resp.text}"
            search_results_type = search_type_resp.json()
            assert any(f["filename"] == pdf_filename for f in search_results_type), "PDF file not found by type search"
            assert all(f["content_type"] == "application/pdf" for f in search_results_type)
            assert len(search_results_type) >= 1