import asyncio
import logging
from typing import Any

import asyncpg

from config import Config

logger = logging.getLogger(__name__)
pool: asyncpg.Pool | None = None


async def init_db(retries: int = 3, delay: int = 2) -> None:
    global pool
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            if pool is None:
                pool = await asyncpg.create_pool(
                    Config.DATABASE_URL,
                    min_size=1,
                    max_size=5,
                    command_timeout=30,
                )
                logger.info("Database pool initialized.")
            return
        except Exception as exc:
            last_error = exc
            logger.exception("Database connection attempt %s failed: %s", attempt + 1, exc)
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    raise RuntimeError("Database initialization failed") from last_error


async def close_db() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def ensure_user_profile(user_id: int) -> None:
    if pool is None:
        logger.warning("Database pool not available. Skipping user profile bootstrap.")
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO user_profiles (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
            user_id,
        )


async def save_asset(user_id: int, image_url: str, prompt: str, caption: str) -> None:
    if pool is None:
        logger.warning("Database pool not available. Skipping save.")
        return
    try:
        await ensure_user_profile(user_id)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO asset_queue (user_id, image_url, prompt, caption)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                image_url,
                prompt,
                caption,
            )
    except Exception as exc:
        logger.exception("Failed to save asset: %s", exc)


async def get_user_style(user_id: int) -> str:
    if pool is None:
        return ""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT style_profile FROM user_profiles WHERE user_id = $1",
                user_id,
            )
            return row["style_profile"] if row else ""
    except Exception as exc:
        logger.exception("Failed to get user style: %s", exc)
        return ""
