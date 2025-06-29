from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)
import logging
from flask import Flask, request
import os
import asyncio

from config import BOT_TOKEN
from keyboards import main_menu
from callback_handlers import handle_main_menu, handle_back_navigation
from message_handlers import handle_all_messages
from bio_handler import (
    select_job, ask_bio_fields, handle_skill_navigation,
    handle_skill_reset, handle_skill_continue, handle_skill_selection, collect_bio
)
from admin_handler import (
    show_country_jobs, handle_job_actions, handle_bio_approval
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Flask app
flask_app = Flask(__name__)
app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(False).build()

# Register bot commands
async def set_bot_commands():
    await app.bot.set_my_commands([
        BotCommand("start", "شروع دوباره"),
    ])

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "درود! 👋\n به راهنمای آرپی R.O.T.C خوش اومدی چه کمکی میتونم بهت بکنم؟",
        reply_markup=main_menu()
    )

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_skill_navigation, pattern="^skill_page_"))
app.add_handler(CallbackQueryHandler(handle_skill_reset, pattern="^reset_skills$"))
app.add_handler(CallbackQueryHandler(handle_skill_continue, pattern="^skills_done$"))
app.add_handler(CallbackQueryHandler(handle_skill_selection, pattern="^select_skill_"))
app.add_handler(CallbackQueryHandler(select_job, pattern="^select_country_"))
app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^job_"))
app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(approve|reject)_bio_"))
app.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_to_previous$"))
app.add_handler(CallbackQueryHandler(handle_main_menu))
app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, collect_bio))
app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & (~filters.COMMAND), handle_all_messages))

# Webhook route
@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), app.bot)
        await app.process_update(update)
        return 'OK', 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

# Setup and run
async def setup():
    await app.initialize()
    await set_bot_commands()
    await app.bot.set_webhook(f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}")
    print(f"✅ Webhook set to: https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}")
    print("✅ Bot is running via webhook with Flask")

# Run everything
if __name__ == "__main__":
    # اجرای setup جداگانه در event loop مخصوص Flask
    asyncio.get_event_loop().create_task(setup())

    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)
