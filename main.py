import asyncio
import os
import logging
import signal
import sys
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)
from telegram.error import Conflict, NetworkError

from config import BOT_TOKEN,PORT
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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler"""
    logger = logging.getLogger(__name__)
    
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance may be running")
        return
    elif isinstance(context.error, NetworkError):
        logger.warning(f"Network error: {context.error}")
        return
    else:
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

def signal_handler(signal_num, frame):
    print(f"\n🛑 Received signal {signal_num}. Shutting down gracefully...")
    sys.exit(0)

# if __name__ == "__main__":
#     os.environ['PYTHONUNBUFFERED'] = "1"
    
#     # Set up signal handlers for graceful shutdown
#     signal.signal(signal.SIGINT, signal_handler)
#     signal.signal(signal.SIGTERM, signal_handler)
    
#     async def on_startup(app):
#         await set_bot_commands(app)

#     app: Application = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    
#     # Webhook support for Render.com deployment (commented out - use polling by default)
#     # Uncomment the webhook section below and comment out the polling section to use webhooks
    
#     # WEBHOOK DEPLOYMENT (for Render.com):
#     RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
#     WEBHOOK_URL = f"https://{RENDER_EXTERNAL_HOSTNAME}/{BOT_TOKEN}"

    
#     async def webhook_main():
#         # Set webhook
#         await app.bot.set_webhook(url=WEBHOOK_URL)
        
#         # Create web application
#         from aiohttp import web, web_runner
        
#         async def handle_webhook(request):
#             data = await request.json()
#             update = Update.to_object(data)  # روش توصیه‌شده در نسخه‌های جدید
#             await app.process_update(update)
#             return web.Response(text="OK")

#         # Setup web server
#         webapp = web.Application()
#         webapp.router.add_post(f"/{BOT_TOKEN}", handle_webhook)
        
#         runner = web_runner.AppRunner(webapp)
#         await runner.setup()
#         site = web_runner.TCPSite(runner, "0.0.0.0", PORT)
        
#         await app.initialize()
#         await app.start()
#         await site.start()
        
#         print(f"✅ Bot is running with webhook on port {PORT}")
        
#         # Keep the server running
#         import asyncio
#         await asyncio.Event().wait()
    
#     if RENDER_EXTERNAL_HOSTNAME:
#         asyncio.run(webhook_main())
#     else:
#     # Add global error handler
#         app.add_error_handler(error_handler)

#     # Setup job queue if available
#     if app.job_queue:
#         app.job_queue.run_repeating(
#             scheduled_cleanup,
#             interval=300,
#             first=10
#         )
#     else:
#         print("⚠️ JobQueue not available - scheduled cleanup disabled")

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

    # POLLING DEPLOYMENT (default):
    # print("✅ Bot is running with polling...")
    # try:
    #     app.run_polling(drop_pending_updates=True)
    # except Exception as e:
    #     print(f"❌ Bot crashed: {e}")
    #     sys.exit(1)

    print(f"✅ Bot is running on port {PORT} via webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}",
    )
