
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)
import logging
from flask import Flask, request
import asyncio
import os
import threading

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

# Flask app for webhook
flask_app = Flask(__name__)

async def set_bot_commands(app):
    commands = [
        BotCommand("start", "شروع دوباره"),
    ]
    await app.bot.set_my_commands(commands)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

pv_filter = filters.ChatType.PRIVATE

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("درود! 👋\n به راهنمای آرپی R.O.T.C خوش اومدی چه کمکی میتونم بهت بکنم؟", reply_markup=main_menu())

# Bot setup
app: Application = ApplicationBuilder().token(BOT_TOKEN).post_init(set_bot_commands).build()

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
app.add_handler(MessageHandler(pv_filter & filters.PHOTO, collect_bio))
app.add_handler(MessageHandler(pv_filter & filters.TEXT & (~filters.COMMAND), handle_all_messages))

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = Update.de_json(json_data, app.bot)

        # Run the coroutine in a new event loop inside a thread
        def run_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(app.process_update(update))
            loop.close()

        threading.Thread(target=run_update).start()

        return 'OK'
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return 'Error', 500

async def setup_webhook():
    """Set up the webhook URL"""
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{BOT_TOKEN}"
    await app.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to: {webhook_url}")

if __name__ == "__main__":
    async def main():
        await app.initialize()
        await setup_webhook()

    asyncio.run(main())

    print("✅ Bot is running via webhook with Flask")

    port = int(os.environ.get('PORT', 5000))
    flask_app.run(host='0.0.0.0', port=port, debug=False)
