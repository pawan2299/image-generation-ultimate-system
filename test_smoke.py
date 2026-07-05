import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db?sslmode=require")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com")
    monkeypatch.setenv("WEBHOOK_PATH", "secret-path")
    monkeypatch.setenv("PORT", "8000")
    yield


def test_config_fallback(env):
    sys.modules.pop("config", None)
    config = importlib.import_module("config")
    assert config.Config.WEBHOOK_URL == "https://example.com"
    assert config.Config.WEBHOOK_PATH == "secret-path"


def test_generate_image_builds_url(env):
    sys.modules.pop("config", None)
    sys.modules.pop("ai_engine", None)
    ai = importlib.import_module("ai_engine")
    import asyncio

    _, url, source = asyncio.run(ai.generate_image("test prompt", "9:16"))
    assert url is not None
    assert "model=flux-realism" in url
    assert "height=1280" in url
    assert source == "Flux-Realism"


def test_schema_contains_pgcrypto():
    schema = (ROOT / "schema.sql").read_text(encoding="utf-8")
    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto;" in schema


def test_database_bootstraps_user_profile(env, monkeypatch):
    sys.modules.pop("database", None)

    class FakeAsyncPG:
        class Pool:
            pass

        async def create_pool(*args, **kwargs):
            return None

    monkeypatch.setitem(sys.modules, "asyncpg", FakeAsyncPG())
    database = importlib.import_module("database")

    calls = []

    class FakeConn:
        async def execute(self, query, *args):
            calls.append((query.strip(), args))

        async def fetchrow(self, query, *args):
            calls.append((query.strip(), args))
            return {"style_profile": ""}

    class FakeAcquire:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquire()

        async def close(self):
            return None

    monkeypatch.setattr(database, "pool", FakePool())
    import asyncio
    asyncio.run(database.save_asset(42, "https://example.com/image.jpg", "prompt", "caption"))

    assert any("INSERT INTO user_profiles" in q for q, _ in calls)
    assert any("INSERT INTO asset_queue" in q for q, _ in calls)


def test_config_missing_raises(monkeypatch):
    for key in ["TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY", "DATABASE_URL", "WEBHOOK_URL", "RENDER_EXTERNAL_URL", "WEBHOOK_PATH", "PORT"]:
        monkeypatch.delenv(key, raising=False)
    sys.modules.pop("config", None)
    with pytest.raises(RuntimeError):
        importlib.import_module("config")
