import asyncio
import os
import logging
from flask import Flask
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)

from config import BOT_TOKEN, PORT
from keyboards import main_menu
from callback_handlers import handle_main_menu, handle_back_navigation
from message_handlers import handle_all_messages
from bio_handler import (
    select_job, ask_bio_fields, handle_skill_navigation,
    handle_skill_reset, handle_skill_continue, handle_skill_selection,
    collect_bio, handle_job_locks
)
from admin_handler import (
    show_country_jobs, handle_job_actions, handle_bio_approval
)
from data_manager import clear_expired_reservations, jobs_by_country

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Flask برای بررسی
flask_app = Flask(__name__)

pv_filter = filters.ChatType.PRIVATE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
        reply_markup=main_menu()
    )

async def set_bot_commands(app):
    commands = [
        BotCommand("start", "شروع دوباره"),
    ]
    await app.bot.set_my_commands(commands)

async def scheduled_cleanup(context: ContextTypes.DEFAULT_TYPE):
    cleared = clear_expired_reservations(jobs_by_country)
    if cleared:
        print(f"🧹 {cleared} رزرو منقضی شده آزاد شد.")

if __name__ == "__main__":
    import asyncio
    os.environ['PYTHONUNBUFFERED'] = "1"
    async def on_startup(app):
        await set_bot_commands(app)

    app: Application = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.job_queue.run_repeating(
        scheduled_cleanup,
        interval=300,
        first=10
    )

    # Add handlers...
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_skill_navigation, pattern="^skill_page_"))
    app.add_handler(CallbackQueryHandler(handle_skill_reset, pattern="^reset_skills$"))
    app.add_handler(CallbackQueryHandler(handle_skill_continue, pattern="^skills_done$"))
    app.add_handler(CallbackQueryHandler(handle_skill_selection, pattern="^select_skill_"))
    app.add_handler(CallbackQueryHandler(select_job, pattern="^select_country_"))
    app.add_handler(CallbackQueryHandler(handle_job_locks, pattern="^job_locked$|^job_taken$"))
    app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^job_"))
    app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
    app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
    app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(approve|reject)_bio_"))
    app.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_to_previous$"))
    app.add_handler(CallbackQueryHandler(handle_main_menu))
    app.add_handler(MessageHandler(pv_filter & filters.PHOTO, collect_bio))
    app.add_handler(MessageHandler(pv_filter & filters.TEXT & (~filters.COMMAND), handle_all_messages))

    print(f"✅ Bot is running on port {PORT} via webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}",
    )
