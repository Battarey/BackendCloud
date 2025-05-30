# paths
import sys
import os
# other
import uuid
import asyncio
import pytest

pytestmark = pytest.mark.asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.main import app
from httpx import AsyncClient

async def test_access_foreign_file():
    unique1 = uuid.uuid4().hex[:8]
    unique2 = uuid.uuid4().hex[:8]
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            user_data1 = {
                "username": f"user1_{unique1}",
                "email": f"user1_{unique1}@ex.com",
                "password": "Test1234!"
            }
            user_data2 = {
                "username": f"user2_{unique2}",
                "email": f"user2_{unique2}@ex.com",
                "password": "Test1234!"
            }
            resp = await ac.post("/users/", json=user_data1)
            assert resp.status_code == 200
            resp = await ac.post("/users/", json=user_data2)
            assert resp.status_code == 200
            resp1 = await ac.post("/users/login", data={"username": user_data1["username"], "password": user_data1["password"]})
            assert resp1.status_code == 200, f"Login failed: {resp1.text}"
            token1 = resp1.json()["access_token"]
            resp2 = await ac.post("/users/login", data={"username": user_data2["username"], "password": user_data2["password"]})
            assert resp2.status_code == 200, f"Login failed: {resp2.text}"
            token2 = resp2.json()["access_token"]
            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}
            files = {"file": ("file1.txt", b"abc", "text/plain")}
            upload = await ac.post("/files/", files=files, headers=headers1)
            assert upload.status_code == 200
            file_id = upload.json()["id"]
            resp = await ac.get(f"/files/{file_id}/info", headers=headers2)
            if resp.status_code == 404:
                resp = await ac.get(f"/files/{file_id}/download", headers=headers2)
            assert resp.status_code in (403, 404)
            resp = await ac.delete(f"/files/{file_id}", headers=headers2)
            assert resp.status_code in (403, 404, 200)

async def test_access_foreign_folder():
    unique1 = uuid.uuid4().hex[:8]
    unique2 = uuid.uuid4().hex[:8]
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            user_data1 = {
                "username": f"user1_{unique1}",
                "email": f"user1_{unique1}@ex.com",
                "password": "Test1234!"
            }
            user_data2 = {
                "username": f"user2_{unique2}",
                "email": f"user2_{unique2}@ex.com",
                "password": "Test1234!"
            }
            resp = await ac.post("/users/", json=user_data1)
            assert resp.status_code == 200
            resp = await ac.post("/users/", json=user_data2)
            assert resp.status_code == 200
            resp1 = await ac.post("/users/login", data={"username": user_data1["username"], "password": user_data1["password"]})
            assert resp1.status_code == 200, f"Login failed: {resp1.text}"
            token1 = resp1.json()["access_token"]
            resp2 = await ac.post("/users/login", data={"username": user_data2["username"], "password": user_data2["password"]})
            assert resp2.status_code == 200, f"Login failed: {resp2.text}"
            token2 = resp2.json()["access_token"]
            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}
            resp = await ac.post("/folders/", json={"name": "folder1"}, headers=headers1)
            assert resp.status_code == 200
            folder_id = resp.json()["id"]
            resp = await ac.get(f"/folders/{folder_id}", headers=headers2)
            assert resp.status_code in (403, 404)
            resp = await ac.delete(f"/folders/{folder_id}", headers=headers2)
            assert resp.status_code in (403, 404)

async def test_upload_exceeding_storage_limit():
    unique = uuid.uuid4().hex[:8]
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            user_data = {
                "username": f"userlimit_{unique}",
                "email": f"userlimit_{unique}@ex.com",
                "password": "Test1234!"
            }
            reg_resp = await ac.post("/users/", json=user_data)
            print(f"Registration response: {reg_resp.status_code} {reg_resp.text}")
            assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
            await asyncio.sleep(0.3)  # Дать БД время на коммит
            resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            print(f"Login response: {resp.status_code} {resp.text}")
            assert resp.status_code == 200, f"Login failed: {resp.text}"
            token = resp.json()["access_token"]
            await asyncio.sleep(0.3)  # Дать БД время на коммит
            headers = {"Authorization": f"Bearer {token}"}
            for _ in range(10):
                resp = await ac.get("/users/me", headers=headers)
                if resp.status_code == 200:
                    break
                await asyncio.sleep(0.5)
            assert resp.status_code == 200, f"/users/me failed: {resp.text}"
            user_id = resp.json()["id"]
            await ac.delete(f"/settings/user/{user_id}", headers=headers)
            settings_data = {"storage_limit": 1, "theme": "system", "language": "en", "notifications_enabled": True}
            await ac.post("/settings/", json=settings_data, headers=headers)
            files = {"file": ("big.txt", b"abc", "text/plain")}
            resp = await ac.post("/files/", files=files, headers=headers)
            assert resp.status_code in (400, 413)
            assert "limit" in resp.text.lower() or "storage" in resp.text.lower()

async def test_invalid_token_access():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            invalid_headers = {"Authorization": "Bearer invalidtoken123"}
            resp = await ac.get("/files/", headers=invalid_headers)
            assert resp.status_code == 401
            resp = await ac.get("/folders/", headers=invalid_headers)
            assert resp.status_code == 401

async def test_access_without_token():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.get("/files/")
            assert resp.status_code == 401
            resp = await ac.get("/folders/")
            assert resp.status_code == 401

async def test_access_nonexistent_object():
    unique = uuid.uuid4().hex[:8]
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            user_data = {
                "username": f"usernotfound_{unique}",
                "email": f"usernotfound_{unique}@ex.com",
                "password": "Test1234!"
            }
            resp = await ac.post("/users/", json=user_data)
            assert resp.status_code == 200
            resp = await ac.post("/users/login", data={"username": user_data["username"], "password": user_data["password"]})
            assert resp.status_code == 200, f"Login failed: {resp.text}"
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            resp = await ac.get(f"/files/00000000-0000-0000-0000-000000000000/info", headers=headers)
            if resp.status_code == 404:
                resp = await ac.get(f"/files/00000000-0000-0000-0000-000000000000/download", headers=headers)
            assert resp.status_code in (404, 403)
            resp = await ac.get(f"/folders/00000000-0000-0000-0000-000000000000", headers=headers)
            assert resp.status_code in (404, 403)
