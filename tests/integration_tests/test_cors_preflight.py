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

@pytest.mark.asyncio
async def test_cors_preflight_download():
    async with app.router.lifespan_context(app):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            file_id = uuid4()
            resp = await ac.options(f"/files/download/{file_id}")
            assert resp.status_code == 200
            assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:3500"
            assert "GET" in resp.headers.get("Access-Control-Allow-Methods", "")
            assert "OPTIONS" in resp.headers.get("Access-Control-Allow-Methods", "")
