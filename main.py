import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
import ai_engine as ai
import database as db
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CAPTION_LIMIT = 900
MESSAGE_LIMIT = 3500

def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "🤖 Autonomous Vision Engine online.\n\n"
        "• Send a text prompt for cinematic generation.\n"
        "• Send an image to start the evolution loop."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    user_id = update.effective_user.id
    raw_prompt = update.message.text or ""
    status = await update.message.reply_text("🧠 Processing prompt...")
    try:
        final_prompt = await ai.enhance_prompt_cinematic(raw_prompt)
        _, url, _ = await ai.generate_image(final_prompt, "16:9")
        if not url:
            await status.edit_text("❌ Render engines failed to return an image URL.")
            return
        await status.delete()
        caption = _truncate(
            f"🎬 Masterpiece rendered.\n\n📝 Prompt: {final_prompt}",
            CAPTION_LIMIT,
        )
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=url,
            caption=caption,
        )
        await db.save_asset(user_id, url, final_prompt, "Cinematic AI Art")
    except Exception:
        logger.exception("Text handler failed")
        await status.edit_text("❌ Request failed. Please try again.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    try:
        await update.message.reply_text("👁️ Analyzing image and starting evolution loop...")
        photo = update.message.photo
        if not photo:
            await update.message.reply_text("❌ No photo found in message.")
            return
        photo_file = await photo[-1].get_file()
        img_bytes = await photo_file.download_as_bytearray()
        context_text = "Initial user provided reference image."
        
        for i in range(1, 4):
            analysis = await ai.vision_director(bytes(img_bytes), context_text)
            if not analysis:
                logger.warning(f"Vision director failed at iteration {i}")
                break
            thought = _truncate(str(analysis.get("thought", "Processing visual data...")), 300)
            next_prompt = str(analysis.get("next_prompt", context_text)).strip() or context_text
            caption = _truncate(str(analysis.get("caption", "AI Evolution")), CAPTION_LIMIT)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔄 Iteration {i}: {thought}",
            )
            
            _, url, _ = await ai.generate_image(next_prompt, "9:16")
            if not url:
                logger.error(f"Image generation failed at iteration {i}")
                break
            
            # Retry logic for send_photo with increased timeout
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=url,
                        caption=caption,
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"send_photo failed (attempt {attempt + 1}), retrying... Error: {e}")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"send_photo failed after {max_retries} attempts: {e}")
                        raise
            
            await db.save_asset(update.effective_user.id, url, next_prompt, caption)
            context_text = next_prompt
            await asyncio.sleep(3)
        
        await update.message.reply_text("✅ Evolution cycle finished.")
    except Exception:
        logger.exception("Photo handler failed")
        await update.message.reply_text("❌ Image processing failed. Please try again.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception: %s", context.error)

async def post_init(application: Application) -> None:
    await db.init_db()
    webhook_url = f"{Config.WEBHOOK_URL.rstrip('/')}/{Config.WEBHOOK_PATH}"
    await application.bot.set_webhook(url=webhook_url)
    logger.info("Webhook configured successfully.")

async def post_shutdown(application: Application) -> None:
    await db.close_db()
    await ai.close_http_client()
    logger.info("Application shutdown complete.")

def main() -> None:
    # [FIX]: Increased timeouts for Telegram requests to prevent ReadTimeout errors
    request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=60.0,      # Increased from default 15s to 60s
        write_timeout=60.0,     # Increased from default 15s to 60s
        connect_timeout=30.0,   # Increased from default 5s to 30s
        pool_timeout=60.0,      # Increased from default 15s to 60s
    )
    
    app = (
        Application.builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .request(request)  # [FIX]: Apply custom request with increased timeouts
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error_handler)
    
    webhook_url = f"{Config.WEBHOOK_URL.rstrip('/')}/{Config.WEBHOOK_PATH}"
    logger.info("Starting webhook server on port %s", Config.PORT)
    logger.info("Webhook configured.")
    
    app.run_webhook(
        listen="0.0.0.0",
        port=Config.PORT,
        url_path=Config.WEBHOOK_PATH,
        webhook_url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    main()