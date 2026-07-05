# Autonomous Vision Engine

A Telegram bot that enhances prompts with Groq, generates image URLs through Pollinations, analyzes images with Gemini, and stores assets in Neon PostgreSQL.

## Required environment variables
- TELEGRAM_BOT_TOKEN
- WEBHOOK_URL
- WEBHOOK_PATH
- GEMINI_API_KEY
- GROQ_API_KEY
- DATABASE_URL
- PORT

## Notes
- The webhook path should be treated as a secret.
- Do not log webhook URLs or API keys.
- Ensure the `schema.sql` file is applied before first startup.
