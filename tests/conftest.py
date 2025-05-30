# paths
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# app
from app.db.database import engine, Base
from app.config import settings
# other 
import pytest
import asyncio

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    if settings.effective_database_url.startswith("sqlite"):
        async def _create():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        asyncio.get_event_loop().run_until_complete(_create())