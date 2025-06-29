from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import logging
import os
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "درود! 👋\n به راهنمای آرپی R.O.T.C خوش اومدی چه کمکی میتونم بهت بکنم؟",
        reply_markup=main_menu()
    )

async def set_bot_commands(application):
    await application.bot.set_my_commands([
        BotCommand("start", "شروع دوباره"),
    ])

if __name__ == "__main__":
    from telegram.ext import Application

    app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(False).build()

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

    async def main():
        await app.initialize()
        await set_bot_commands(app)
        webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}"
        await app.bot.set_webhook(webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")

        # Start built-in webhook server
        await app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            webhook_url=webhook_url,
        )

    import asyncio
    asyncio.run(main())
