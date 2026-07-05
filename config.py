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
    GROQ_API_KEY: str = _required("GROQ_API_KEY")
    DATABASE_URL: str = _required("DATABASE_URL")
    
    # ==========================================
    # GEMINI MULTI-KEY & MULTI-MODEL CONFIG
    # ==========================================
    # Parse comma-separated keys from GEMINI_API_KEYS
    _gemini_keys_str = os.getenv("GEMINI_API_KEYS", "")
    GEMINI_API_KEYS: list[str] = [k.strip() for k in _gemini_keys_str.split(",") if k.strip()]
    
    # Fallback to single GEMINI_API_KEY if multi-key is not provided
    if not GEMINI_API_KEYS:
        single_key = os.getenv("GEMINI_API_KEY", "").strip()
        if single_key:
            GEMINI_API_KEYS = [single_key]
        else:
            raise RuntimeError("Missing required environment variable: GEMINI_API_KEYS (comma-separated) or GEMINI_API_KEY")
            
    # Priority list of models for fallback (Latest & Smartest First, High TPM Fallback Last)
    GEMINI_MODELS: list[str] = [
        "gemini-3.5-flash",       # 1. Latest & Smartest (10 RPM, 250k TPM) - Best Vision Quality
        "gemini-3.1-flash-lite",  # 2. Latest Fast (15 RPM, 250k TPM) - High Speed
        "gemini-2.5-flash",       # 3. Previous Gen Stable (10 RPM, 250k TPM)
        "gemini-2.5-flash-lite",  # 4. Previous Gen Fast (15 RPM, 250k TPM)
        "gemini-2.0-flash",       # 5. Ultimate Emergency Fallback (15 RPM, 1M TPM) - Massive token limit for heavy images
    ]
    
    WEBHOOK_URL: str = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL", "")).strip()
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "telegram-webhook").strip() or "telegram-webhook"
    PORT: int = int(os.getenv("PORT", "8000"))
    
    if not WEBHOOK_URL:
        raise RuntimeError("Missing required environment variable: WEBHOOK_URL or RENDER_EXTERNAL_URL")