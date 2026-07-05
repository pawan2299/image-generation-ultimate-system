import os
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class Config:
    TELEGRAM_BOT_TOKEN: str = _required("TELEGRAM_BOT_TOKEN")
    GEMINI_API_KEY: str = _required("GEMINI_API_KEY")
    GROQ_API_KEY: str = _required("GROQ_API_KEY")
    DATABASE_URL: str = _required("DATABASE_URL")

    WEBHOOK_URL: str = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL", "")).strip()
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "telegram-webhook").strip() or "telegram-webhook"
    PORT: int = int(os.getenv("PORT", "8000"))

    if not WEBHOOK_URL:
        raise RuntimeError("Missing required environment variable: WEBHOOK_URL or RENDER_EXTERNAL_URL")
