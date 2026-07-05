import asyncpg
import logging
from config import Config

logger = logging.getLogger(__name__)
pool = None

# [R&D CONTEXT]: We use a Connection Pool instead of single connections.
# This prevents database overload when multiple users trigger the bot simultaneously.
async def init_db():
    global pool
    if not pool:
        try:
            pool = await asyncpg.create_pool(Config.DATABASE_URL, min_size=1, max_size=10)
            logger.info("✅ Neon.tech Database Pool Initialized.")
        except Exception as e:
            logger.error(f"❌ Database Connection Failed: {e}")

async def save_asset(user_id: int, image_url: str, prompt: str, caption: str):
    """Saves the curated masterpiece to the Instagram Staging Queue."""
    if not pool: return
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO asset_queue (user_id, image_url, prompt, caption)
            VALUES ($1, $2, $3, $4)
        """, user_id, image_url, prompt, caption)

async def get_user_style(user_id: int) -> str:
    """Retrieves user's learned aesthetic preferences."""
    if not pool: return ""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT style_profile FROM user_profiles WHERE user_id = $1", user_id)
        return row['style_profile'] if row else ""
