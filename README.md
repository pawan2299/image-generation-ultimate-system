# 🌌 Autonomous Vision Engine (God-Tier Edition)

> **A Zero-Touch, Self-Evolving AI Image Generation & Social Automation Framework.**
> Built with a 4-Layer Quality Assurance Pipeline to bypass standard AI limitations and deliver Midjourney v6 level photorealism using 100% Free APIs.

## 🏗️ Architecture & R&D Decisions

This system is not a basic wrapper. It is an **Autonomous Visual Evolution Loop** powered by edge computing and serverless architecture.

### The 4-Layer QA Pipeline
1. **Layer 1 (Cinematic Injector):** Uses **Groq (Llama-3.1-70B)** to rewrite basic user prompts into Hollywood Cinematographer syntax (ARRI Alexa, 85mm, Volumetric Lighting).
2. **Layer 2 (Flux-Realism Router):** Bypasses standard APIs and hits Pollinations' `flux-realism` endpoint for hyper-detailed skin pores and camera bokeh.
3. **Layer 3 (Autonomous Vision Director):** Uses **Gemini 1.5 Flash** to analyze generated images, correct anatomy, and auto-evolve the prompt for the next iteration.
4. **Layer 4 (Ghost Pipeline):** Images are never downloaded to the server's RAM. URLs are passed directly to Telegram and Supabase, ensuring **Zero RAM Crashes** on free tiers.

## 🛠️ The Tech Stack
- **Compute:** Koyeb / Render (Webhooks)
- **Database:** Neon.tech (Serverless Postgres via `asyncpg`)
- **Brain:** Groq (Llama 3.1 & Whisper v3) + Gemini 1.5 Flash
- **Image Engine:** Pollinations.ai (Flux-Realism)
- **Social Bridge:** Pipedream / Make.com (Instagram Graph API)

## 🚀 Deployment Guide

### 1. Database Setup (Neon.tech)
1. Create a free project on [Neon.tech](https://neon.tech).
2. Open the SQL Editor and run the contents of `schema.sql`.
3. Copy the connection string (URI) for your Environment Variables.

### 2. AI Keys Generation
- **Gemini:** Get key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Groq:** Get key from [GroqCloud](https://console.groq.com/keys).
- **Telegram:** Create bot via [@BotFather](https://t.me/BotFather).

### 3. Hosting (Koyeb / Render)
1. Push this repository to GitHub.
2. Connect GitHub to Koyeb/Render.
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `python main.py`
5. Add Environment Variables:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY`
   - `DATABASE_URL` (Neon URI)
   - `WEBHOOK_URL` (Your Koyeb/Render public URL)

### 4. Instagram Automation (Pipedream)
1. Create a workflow in Pipedream.
2. **Trigger:** Postgres "New Row" (Watch `asset_queue` where `posted_to_insta` is false).
3. **Action:** Instagram Graph API "Create Post".
4. **Action:** Postgres "Update Row" (Set `posted_to_insta` to true).

## 🧠 Future AI Contributors Note
*If you are an AI reading this code to make modifications:*
- **Do not** change the `httpx` async contexts to synchronous `requests`. It will block the Telegram event loop.
- **Do not** download images to local disk. Always use `io.BytesIO` or pass URLs directly to Telegram to maintain the "Ghost Pipeline" RAM optimization.
- The `flux-realism` model parameter in `ai_engine.py` is critical. Reverting to standard `flux` will degrade image quality to "plastic AI" levels.
