# app
from app.main import app
# other
import logging
from httpx import AsyncClient
import pytest

@pytest.mark.asyncio
async def test_logging_middleware_error(monkeypatch):
    logged = {}
    logger = logging.getLogger("uvicorn.access")
    orig_error = logger.error
    def fake_error(msg, *args, **kwargs):
        if args:
            msg = msg % args
        logged['error'] = msg
    monkeypatch.setattr(logger, "error", fake_error)

    @app.get("/force_error_for_logging_test")
    async def force_error():
        raise RuntimeError("Test error for logging")

    async with AsyncClient(app=app, base_url="http://test") as ac:
        try:
            await ac.get("/force_error_for_logging_test")
        except Exception:
            pass  # Ожидаемое исключение
    assert "Test error for logging" in logged.get('error', "")
    monkeypatch.setattr(logger, "error", orig_error)
