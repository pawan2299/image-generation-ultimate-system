import asyncio
import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter
from config import Config
import database as db
import ai_engine as ai

# [R&D CONTEXT]: Standard Python logging configured for production monitoring.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Autonomous Vision Engine (God-Tier Edition) Online*\n\n"
        "• Send a *Text Prompt* for Cinematic Generation.\n"
        "• Send an *Image* to start the Autonomous Evolution Loop.\n"
        "• Send a *Voice Note* for lazy generation.", parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw_prompt = update.message.text
    
    msg = await update.message.reply_text("🧠 *Layer 1:* Injecting Cinematic Syntax via Groq...", parse_mode="Markdown")
    
    # Layer 1: Enhance Prompt
    final_prompt = await ai.enhance_prompt_cinematic(raw_prompt)
    await msg.edit_text(f"🎨 *Layer 2:* Rendering via Flux-Realism...\n`{final_prompt}`", parse_mode="Markdown")
    
    # Layer 2: Generate Image
    img_bytes, url, source = await ai.generate_image(final_prompt, "16:9")
    
    if img_bytes:
        await msg.delete()
        # Layer 4 (Implicit): Telegram handles the delivery.
        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=url, # Sending URL directly saves RAM (Ghost Pipeline)
            caption=f"🎬 *Masterpiece Rendered*\n📝 *Cinematic Prompt:* {final_prompt}",
            parse_mode="Markdown"
        )
        # Save to Insta Queue
        await db.save_asset(user_id, url, final_prompt, "Cinematic AI Art #AI #Render")
    else:
        await msg.edit_text("❌ Render Engines failed to respond.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """The Autonomous Visual Evolution Loop (Krishna Flow)"""
    await update.message.reply_text("👁️ *Vision Director* is analyzing your image... Starting Evolution Loop.", parse_mode="Markdown")
    
    photo_file = await update.message.photo[-1].get_file()
    img_bytes = await photo_file.download_as_bytearray()
    context_text = "Initial user provided reference image."
    
    # Loop 3 times for demonstration of the Evolution Engine
    for i in range(1, 4): 
        # Layer 3: Vision Director Analysis
        analysis = await ai.vision_director(bytes(img_bytes), context_text)
        if not analysis: break
        
        thought = analysis.get("thought", "Processing visual data...")
        next_prompt = analysis.get("next_prompt", context_text)
        caption = analysis.get("caption", "AI Evolution")
        
        await context.bot.send_message(
            update.effective_chat.id, 
            f"🧠 *Iteration {i} Thought:* {thought}\n🎨 *Generating Upgrade...*", 
            parse_mode="Markdown"
        )
        
        img_bytes, url, source = await ai.generate_image(next_prompt, "9:16")
        if img_bytes:
            await context.bot.send_photo(
                update.effective_chat.id,
                photo=url,
                caption=f"🔄 *Evolution {i}*\n{caption}"
            )
            await db.save_asset(update.effective_user.id, url, next_prompt, caption)
            context_text = next_prompt
            await asyncio.sleep(3) # Telegram Anti-Spam protection
        else:
            break
            
    await update.message.reply_text("✅ *Evolution Cycle Complete.* Top assets queued for Instagram Pipeline.", parse_mode="Markdown")

async def post_init(application: Application):
    """[R&D CONTEXT]: Registers the Webhook on Koyeb/Render startup."""
    webhook_url = f"{Config.WEBHOOK_URL}/{Config.TELEGRAM_BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook successfully set to {webhook_url}")

def main():
    # Initialize Database Pool
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(db.init_db())

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # [R&D CONTEXT]: Run webhook to keep server alive and listen to Telegram pushes.
    app.run_webhook(
        listen="0.0.0.0",
        port=Config.PORT,
        url_path=Config.TELEGRAM_BOT_TOKEN,
        webhook_url=f"{Config.WEBHOOK_URL}/{Config.TELEGRAM_BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
