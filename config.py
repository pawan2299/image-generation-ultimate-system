import os
from dotenv import load_dotenv

# [R&D CONTEXT]: Load .env file for local testing. 
# On Render, it will automatically read from the dashboard's Environment Variables.
load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # AI Engines
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Database (Neon.tech)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Server / Render Config
    PORT: int = int(os.getenv("PORT", 8000))
    WEBHOOK_URL: str = os.getenv("RENDER_EXTERNAL_URL", "") 
    # Note: Render automatically injects RENDER_EXTERNAL_URL, we just read it here.
