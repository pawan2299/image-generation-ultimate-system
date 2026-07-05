import os
from dotenv import load_dotenv

# [R&D CONTEXT]: Load environment variables from .env file for local testing.
# In production (Koyeb/Render), these are injected directly by the hosting platform.
load_dotenv()

class Config:
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "") # e.g., https://your-app.koyeb.app
    
    # AI Engines (The God-Tier Stack)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "") # For Vision Director & Fallback
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")     # For Lightning-fast Whisper & Prompt Injection
    
    # Database (Neon.tech Serverless Postgres)
    # Format: postgresql://user:password@host/dbname?sslmode=require
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # System Configurations
    PORT: int = int(os.getenv("PORT", 8000))
