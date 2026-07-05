import asyncpg
import logging
import asyncio
from config import Config

logger = logging.getLogger(__name__)
pool = None

# [R&D CONTEXT]: Retry logic for Render cold starts where DNS resolution might fail initially
async def init_db(retries=3, delay=2):
    global pool
    for attempt in range(retries):
        try:
            if not pool:
                pool = await asyncpg.create_pool(Config.DATABASE_URL, min_size=1, max_size=10)
                logger.info("✅ Neon.tech Database Pool Initialized.")
            return  # Success, exit function
        except Exception as e:
            logger.error(f"❌ Database Connection Attempt {attempt + 1} Failed: {e}")
            if attempt < retries - 1:
                logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error("❌ All database connection attempts failed. Bot will run without DB.")

async def save_asset(user_id: int, image_url: str, prompt: str, caption: str):
    """Saves the curated masterpiece to the Instagram Staging Queue."""
    if not pool: 
        logger.warning("⚠️ Database pool not available. Skipping save.")
        return
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO asset_queue (user_id, image_url, prompt, caption)
                VALUES ($1, $2, $3, $4)
            """, user_id, image_url, prompt, caption)
    except Exception as e:
        logger.error(f"❌ Failed to save asset: {e}")

async def get_user_style(user_id: int) -> str:
    """Retrieves user's learned aesthetic preferences."""
    if not pool: return ""
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT style_profile FROM user_profiles WHERE user_id = $1", user_id)
            return row['style_profile'] if row else ""
    except Exception as e:
        logger.error(f"❌ Failed to get user style: {e}")
        return ""