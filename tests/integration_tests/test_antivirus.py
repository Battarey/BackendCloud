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
async def test_antivirus_blocks_infected_file(
    monkeypatch
):
    # Checks that the antivirus blocks the download of an infected file (emulated via monkeypatch scan_bytes_for_viruses)
    from fastapi import HTTPException
    async def fake_scan_bytes_for_viruses(data):
        raise HTTPException(status_code=400, detail="Virus detected!")
    # Monkeypatch by usage location in upload_file
    monkeypatch.setattr('app.routes.files.scan_bytes_for_viruses', fake_scan_bytes_for_viruses)
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            unique = uuid.uuid4().hex[:8]
            user_data = {
                "username": f"virususer_{unique}",
                "email": f"virususer_{unique}@example.com",
                "password": "Test1234!"
            }
            resp_reg = await ac.post("/users/", json=user_data)
            assert resp_reg.status_code == 200, f"User create failed: {resp_reg.text}"
            login = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert login.status_code == 200, f"Login failed: {login.text}"
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            # Settings are already created during registration, no need to recreate them
            # Attempt to download "infected" file
            files = {"file": ("virus.txt", b"malicious content", "text/plain")}
            resp = await ac.post("/files/", files=files, headers=headers)
            assert resp.status_code in (400, 409, 422), f"Antivirus should block infected file, got {resp.status_code}"
