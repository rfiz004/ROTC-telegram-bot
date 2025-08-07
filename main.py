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
from telegram.error import Conflict, NetworkError, TelegramError

from config import BOT_TOKEN, PORT, GITHUB_REPO, GITHUB_TOKEN, GITHUB_BRANCH
from keyboards import main_menu
from callback_handlers import handle_main_menu, handle_back_navigation, handle_back_to_country_menu, food_handle_callback
from message_handlers import handle_all_messages
from admin_province_handler import handle_province_edit, admin_view_shop_items, run_food_processing
from shop_handler import handle_shop_buy, handle_quantity_input
import subprocess
import traceback
from auto_commit_push import schedule_auto_push
from admin_handler import cleanup_incomplete_bio_for_user
from data_manager import save_bios
from admin_province_handler import back_to_admin_menu, admin_lock_shop, toggle_block_country
from province_handler import show_grain_preview, edit_tax_callback, handle_tax_input
from run_git_push import run_git_push

async def periodic_git_push():
    while True:
        logger.info("🔄 Running scheduled git push...")
        await asyncio.get_running_loop().run_in_executor(None, run_git_push)
        await asyncio.sleep(15 * 60)

# Import handlers with proper error handling
try:
    from bio_handler import (
        select_job, ask_bio_fields, handle_skill_navigation,
        handle_skill_reset, handle_skill_continue, handle_skill_selection,
        collect_bio, handle_job_locks, start_bio_submission
    )
except ImportError as e:
    logging.warning(f"Bio handlers not available: {e}")
    # Create safe dummy functions
    async def select_job(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")
    async def ask_bio_fields(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")
    async def handle_skill_navigation(*args, **kwargs):
        await args[0].callback_query.edit_message_text("انتخاب مهارت در حال حاضر در دسترس نیست.")
    async def handle_skill_reset(*args, **kwargs):
        await args[0].callback_query.edit_message_text("انتخاب مهارت در حال حاضر در دسترس نیست.")
    async def handle_skill_continue(*args, **kwargs):
        await args[0].callback_query.edit_message_text("انتخاب مهارت در حال حاضر در دسترس نیست.")
    async def handle_skill_selection(*args, **kwargs):
        await args[0].callback_query.edit_message_text("انتخاب مهارت در حال حاضر در دسترس نیست.")
    async def collect_bio(*args, **kwargs):
        await args[0].message.reply_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")
    async def handle_job_locks(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")
    async def start_bio_submission(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")

try:
    from admin_handler import (
        show_admin_menu, show_admin_job_list, show_admin_skill_list,
        show_country_jobs, handle_job_actions, handle_skill_actions,
        handle_bio_approval, show_pending_bios, handle_admin_text_message
    )
except ImportError as e:
    logging.warning(f"Admin handlers not available: {e}")
    async def show_admin_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ادمین پنل در حال حاضر در دسترس نیست.")
    async def show_admin_job_list(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مشاغل در حال حاضر در دسترس نیست.")
    async def show_country_jobs(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مشاغل در حال حاضر در دسترس نیست.")
    async def handle_job_actions(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مشاغل در حال حاضر در دسترس نیست.")
    async def handle_bio_approval(*args, **kwargs):
        await args[0].callback_query.edit_message_text("تایید بیوگرافی در حال حاضر در دسترس نیست.")
    async def show_pending_bios(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مشاهده بیوگرافی‌های در انتظار در حال حاضر در دسترس نیست.")
    async def handle_admin_text_message(*args, **kwargs):
        await args[0].message.reply_text("ادمین پنل در حال حاضر در دسترس نیست.")
    async def show_admin_skill_list(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مهارت‌ها در حال حاضر در دسترس نیست.")
    async def handle_skill_actions(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مهارت‌ها در حال حاضر در دسترس نیست.")

# Import other handlers with error handling
try:
    from admin_province_handler import (
        show_admin_province_menu, show_all_provinces, view_province_admin,
        admin_manage_transfers, approve_transfer, reject_transfer,
        admin_manage_shop, admin_add_shop_item_prompt,
        handle_shop_item_text_input, handle_shop_item_image,
        show_country_admin_menu, show_country_provinces, show_country_transfers,
        admin_edit_shop_item, admin_delete_shop_item, confirm_delete_shop_item, handle_shop_edit_choice,
        show_admin_shop_page, handle_new_shop_caption, handle_new_shop_image,
        show_weekly_processing_menu, preview_weekly_processing, run_weekly_processing,
        admin_show_economy_overview
    )
except ImportError as e:
    logging.warning(f"Admin province handlers not available: {e}")
    async def show_admin_province_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def show_all_provinces(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def view_province_admin(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def admin_manage_transfers(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت انتقالات در حال حاضر در دسترس نیست.")
    async def approve_transfer(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت انتقالات در حال حاضر در دسترس نیست.")
    async def reject_transfer(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت انتقالات در حال حاضر در دسترس نیست.")
    async def admin_manage_shop(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def admin_add_shop_item_prompt(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_shop_item_text_input(*args, **kwargs):
        await args[0].message.reply_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_shop_item_image(*args, **kwargs):
        await args[0].message.reply_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def show_country_admin_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def show_country_provinces(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def show_country_transfers(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def admin_edit_shop_item(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def admin_delete_shop_item(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def confirm_delete_shop_item(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_shop_edit_choice(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def show_admin_shop_page(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_new_shop_caption(*args, **kwargs):
        return False
    async def handle_new_shop_image(*args, **kwargs):
         await args[0].message.reply_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
    async def show_weekly_processing_menu(*args, **kwargs):
         await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def preview_weekly_processing(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def run_weekly_processing(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
    async def admin_show_economy_overview(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")

try:
    from country_handler import (
        check_password, handle_country_menu, collect_character_name, 
        collect_news_text, select_country_province, handle_user_text, 
        manage_select_country, open_manage_country
    )
except ImportError as e:
    logging.warning(f"Country handlers not available: {e}")
    async def check_password(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def handle_country_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def collect_character_name(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def collect_news_text(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def select_country_province(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def handle_user_text(*args, **kwargs):
        pass  # This is handled by message_handlers.py routing
    async def manage_select_country(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def open_manage_country(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def handle_country_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def collect_character_name(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def collect_news_text(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def select_country_province(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def handle_user_text(*args, **kwargs):
        await args[0].message.reply_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def manage_select_country(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")
    async def open_manage_country(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")

try:
    from shop_handler import (
        open_shop_menu, show_shop_category, show_shop_items_page, 
        handle_item_purchase, confirm_purchase, handle_quantity_input
    )
except ImportError as e:
    logging.warning(f"Shop handlers not available: {e}")
    async def open_shop_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
    async def show_shop_category(*args, **kwargs):
        await args[0].callback_query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
    async def show_shop_items_page(*args, **kwargs):
        await args[0].callback_query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_item_purchase(*args, **kwargs):
        await args[0].callback_query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
    async def confirm_purchase(*args, **kwargs):
        await args[0].callback_query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
    async def handle_quantity_input(*args, **kwargs):
        await args[0].message.reply_text("فروشگاه در حال حاضر در دسترس نیست.")
        return False

try:
    from transfer_handler import (
        show_transfer_menu, show_domestic_transfer, show_international_transfer,
        show_transfer_items, show_transfer_category_items, handle_transfer_quantity, 
        process_transfer_request
    )
except ImportError as e:
    logging.warning(f"Transfer handlers not available: {e}")
    async def show_transfer_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def show_domestic_transfer(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def show_international_transfer(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def show_transfer_items(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def show_transfer_category_items(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def handle_transfer_quantity(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
    async def process_transfer_request(*args, **kwargs):
        await args[0].callback_query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")



from data_manager import clear_expired_reservations, jobs_by_country, load_data_file, save_data_file

# ────────────── Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

pv_filter = filters.ChatType.PRIVATE

# ────────────── Bot Commands
# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     try:
#         # Clear any existing user state
#         user_id = update.message.from_user.id
#         if user_id in context.user_data:
#             context.user_data[user_id].clear()

#         await update.message.reply_text(
#             "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
#             reply_markup=main_menu()
#         )
#     except Exception as e:
#         logger.error(f"Error in start command: {e}")
#         try:
#             await update.message.reply_text("خطایی رخ داد. لطفاً مجدداً تلاش کنید.")
#         except:
#             pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id

        # 🧹 حذف بیوی ناقص در صورت وجود
        await cleanup_incomplete_bio_for_user(update, context)

        # 🧼 پاکسازی وضعیت قبلی کاربر
        # if user_id in context.user_data:
        #     context.user_data[user_id].clear()

        # 🧼 پاکسازی وضعیت قبلی کاربر
        if user_id in context.user_data:
            context.user_data[user_id].clear()
        
        # 👋 پیام خوش‌آمد
        await update.message.reply_text(
            "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
            reply_markup=main_menu()
        )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        try:
            await update.message.reply_text("خطایی رخ داد. لطفاً مجدداً تلاش کنید.")
        except:
            pass

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(f"🆔 آیدی این چت: `{update.effective_chat.id}`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in get_chat_id: {e}")

async def set_bot_commands(app):
    try:
        commands = [
            BotCommand("start", "شروع دوباره"),
            BotCommand("id", "نمایش آیدی چت"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands set successfully")
    except Exception as e:
        logger.error(f"Error setting bot commands: {e}")


async def start_bot_and_scheduler():
    await asyncio.gather(
        main(),
        auto_push_every_15_minutes()
    )

# ────────────── Message Routing
async def handle_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        user_data = context.user_data.get(user_id, {})
        state = user_data.get("state")
        step = user_data.get("step")
        flow_type = user_data.get("flow_type")

        logger.info(f"Text router - User {user_id}: flow_type={flow_type}, state={state}, step={step}")

        # Handle transfer items input
        if step == "awaiting_transfer_items_input":
            from transfer_handler import handle_transfer_items_input
            if await handle_transfer_items_input(update, context):
                return

        # Handle country management flow first
        if flow_type == "country_management":
            if state in ["awaiting_password", "awaiting_character_name", "awaiting_news_text"]:
                await handle_user_text(update, context)
                return

            # Handle tax input
            elif step == "editing_province_tax":
                if await handle_tax_input(update, context):
                    return
            else:
                await update.message.reply_text("لطفاً از منوی کشور استفاده کنید.")
                return

        # Handle shop quantity input
        elif step == "awaiting_quantity" and flow_type == "shop_purchase":
            if await handle_quantity_input(update, context):
                return

        # Handle admin functions
        elif step in ["awaiting_rp_password", "awaiting_skill_name", "removing_skill", "add_job", "remove_job", "increase_job", "decrease_job"]:
            await handle_all_messages(update, context)
            return

        # Handle shop item text inputs
        elif step in ["awaiting_shop_item_name", "awaiting_shop_item_type", "awaiting_shop_item_country", "awaiting_shop_item_description", "awaiting_shop_item_price", "awaiting_shop_item_owner"]:
            await handle_shop_item_text_input(update, context)
            return

        # Handle shop item editing
        elif step == "awaiting_new_shop_caption":
            from admin_province_handler import handle_new_shop_caption
            if await handle_new_shop_caption(update, context):
                return

        # Handle province editing inputs
        elif step and step.startswith("awaiting_province_") and step.endswith("_edit"):
            from admin_province_handler import handle_province_edit_input
            if await handle_province_edit_input(update, context):
                return

        
        # Handle bio flow
        elif flow_type == "bio":
            await collect_bio(update, context)
            return

        # Handle grain management input
        elif flow_type == "grain_management":
            if step == "awaiting_grain_priority":
                from data_manager import handle_grain_priority
                if await handle_grain_priority(update, context):
                    return

            elif step == "awaiting_grain_percentage":
                from data_manager import handle_grain_percentage
                if await handle_grain_percentage(update, context):
                    return


        
        # Default case
        else:
            await update.message.reply_text("برای شروع دستور /start را بزنید.")

    except Exception as e:
        import traceback
        logger.error("Error in text router:\n" + traceback.format_exc())
        try:
            await update.message.reply_text("خطایی رخ داد. لطفاً مجدداً تلاش کنید.")
        except:
            pass

async def handle_photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads"""
    try:
        user_id = update.message.from_user.id
        user_data = context.user_data.get(user_id, {})
        step = user_data.get("step")

        # Handle shop item image upload
        if step == "awaiting_shop_item_image":
            await handle_shop_item_image(update, context)
        elif step == "awaiting_new_shop_image":
            from admin_province_handler import handle_new_shop_image
            await handle_new_shop_image(update, context)
        # Handle bio photo
        else:
            await collect_bio(update, context)
    except Exception as e:
        logger.error(f"Error in photo router: {e}")

# ────────────── Scheduled Jobs
async def scheduled_cleanup(context: ContextTypes.DEFAULT_TYPE):
    try:
        from timer_manager import should_run_task, update_task_time

        # Only run cleanup if enough time has passed (e.g., every hour)
        if should_run_task("last_cleanup", interval_hours=1):
            cleared = clear_expired_reservations(jobs_by_country)
            if cleared:
                logger.info(f"🧹 {cleared} رزرو منقضی شده آزاد شد.")
            update_task_time("last_cleanup")

    except Exception as e:
        logger.error(f"Error in scheduled cleanup: {e}")

# ────────────── Error Handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.warning("Bot conflict detected - another instance may be running")
    elif isinstance(context.error, NetworkError):
        logger.warning(f"Network error: {context.error}")
    elif isinstance(context.error, TelegramError):
        logger.error(f"Telegram API error: {context.error}")
    else:
        logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

# ────────────── Build Application
def create_application():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).post_init(set_bot_commands).build()

        # Add handlers with proper priority
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("id", get_chat_id))

        # ────────────── Handler Priority Order (Most Specific First)

        # 1️⃣ Bio and Skill Handlers (Most specific patterns first)
        app.add_handler(CallbackQueryHandler(handle_skill_navigation, pattern="^skill_page_"))
        app.add_handler(CallbackQueryHandler(handle_skill_reset, pattern="^reset_skills$"))
        app.add_handler(CallbackQueryHandler(handle_skill_continue, pattern="^skills_done$"))
        app.add_handler(CallbackQueryHandler(handle_skill_selection, pattern="^select_skill_"))
        app.add_handler(CallbackQueryHandler(handle_job_locks, pattern="^job_locked$|^job_taken$|^job_azure_locked$"))
        app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^bio_job_"))
        app.add_handler(CallbackQueryHandler(select_job, pattern="^select_bio_country_"))

        # 2️⃣ Admin Handlers
        app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
        app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
        app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(approve|reject)_bio_"))
        app.add_handler(CallbackQueryHandler(handle_skill_actions, pattern="^(add|remove)_skill$"))
        app.add_handler(CallbackQueryHandler(back_to_admin_menu, pattern="^back_to_admin_menu$"))
        app.add_handler(CallbackQueryHandler(run_food_processing, pattern="^run_food_processing$"))
        app.add_handler(CallbackQueryHandler(food_handle_callback, pattern="^(set_grain_priority|set_grain_consumption|preview_grain_effect|manage_food_menu)$"))







        # 3️⃣ Skill Type Selection
        from callback_handlers import handle_skill_type_selection
        app.add_handler(CallbackQueryHandler(handle_skill_type_selection, pattern="^skill_type_"))

        # 4️⃣ Multi-Country Admin Handlers
        app.add_handler(CallbackQueryHandler(show_country_admin_menu, pattern="^admin_country_menu_"))
        app.add_handler(CallbackQueryHandler(show_country_provinces, pattern="^admin_country_provinces_"))
        app.add_handler(CallbackQueryHandler(show_country_transfers, pattern="^admin_country_transfers_"))

        # 5️⃣ Admin Province Management
        app.add_handler(CallbackQueryHandler(edit_tax_callback, pattern="^edit_tax$"))
        app.add_handler(CallbackQueryHandler(show_admin_province_menu, pattern="^admin_province_menu$"))
        app.add_handler(CallbackQueryHandler(admin_view_shop_items, pattern="^admin_view_shop_items$"))
        app.add_handler(CallbackQueryHandler(show_grain_preview, pattern="^preview_grain_effect$"))
        app.add_handler(CallbackQueryHandler(show_all_provinces, pattern="^admin_view_all_provinces$"))
        app.add_handler(CallbackQueryHandler(view_province_admin, pattern="^admin_view_province_"))
        app.add_handler(CallbackQueryHandler(admin_manage_transfers, pattern="^admin_manage_transfers$"))
        app.add_handler(CallbackQueryHandler(handle_province_edit, pattern="^edit_province_"))
        app.add_handler(CallbackQueryHandler(approve_transfer, pattern="^approve_transfer_"))
        app.add_handler(CallbackQueryHandler(reject_transfer, pattern="^reject_transfer_"))
        app.add_handler(CallbackQueryHandler(admin_manage_shop, pattern="^admin_manage_shop$"))
        app.add_handler(CallbackQueryHandler(admin_add_shop_item_prompt, pattern="^admin_add_shop_item$"))
        app.add_handler(CallbackQueryHandler(show_weekly_processing_menu, pattern="^show_weekly_menu$"))
        app.add_handler(CallbackQueryHandler(preview_weekly_processing, pattern="^preview_weekly_processing$"))
        app.add_handler(CallbackQueryHandler(run_weekly_processing, pattern="^run_weekly_processing$"))
        app.add_handler(CallbackQueryHandler(admin_show_economy_overview, pattern="^admin_economy_overview"))
        app.add_handler(CallbackQueryHandler(admin_edit_shop_item, pattern="^admin_edit_shop_item_"))
        app.add_handler(CallbackQueryHandler(admin_delete_shop_item, pattern="^admin_delete_shop_item_"))
        app.add_handler(CallbackQueryHandler(confirm_delete_shop_item, pattern="^confirm_delete_shop_item_"))
        app.add_handler(CallbackQueryHandler(handle_shop_edit_choice, pattern="^edit_shop_(image|caption)$"))

        # 6️⃣ Shop Handlers
        app.add_handler(CallbackQueryHandler(show_shop_category, pattern="^shop_category_"))
        app.add_handler(CallbackQueryHandler(show_shop_items_page, pattern="^shop_page_"))
        # app.add_handler(CallbackQueryHandler(handle_shop_buy, pattern="^shop_buy_"))
        app.add_handler(CallbackQueryHandler(handle_item_purchase, pattern="^buy_item_"))
        app.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_purchase$"))

        # 7️⃣ Transfer Handlers
        app.add_handler(CallbackQueryHandler(show_transfer_menu, pattern="^transfer_menu$"))
        app.add_handler(CallbackQueryHandler(show_domestic_transfer, pattern="^transfer_domestic$"))
        app.add_handler(CallbackQueryHandler(show_international_transfer, pattern="^transfer_international$"))
        app.add_handler(CallbackQueryHandler(show_transfer_items, pattern="^(domestic|international)_target_"))
        app.add_handler(CallbackQueryHandler(show_transfer_category_items, pattern="^transfer_category_"))
        app.add_handler(CallbackQueryHandler(handle_transfer_quantity, pattern="^transfer_item_"))
        app.add_handler(CallbackQueryHandler(process_transfer_request, pattern="^confirm_transfer_request$"))

        # Add view pending transfers handler
        try:
            from transfer_handler import view_pending_transfers
            app.add_handler(CallbackQueryHandler(view_pending_transfers, pattern="^view_pending_transfers$"))
        except ImportError:
            pass

        # 8️⃣ Country Management
        app.add_handler(CallbackQueryHandler(manage_select_country, pattern="^manage_select_country_"))
        app.add_handler(CallbackQueryHandler(select_country_province, pattern="^province\\|"))

        # 9️⃣ Country Menu Operations
        app.add_handler(CallbackQueryHandler(handle_country_menu, pattern="^country_|^news_|^economy_|^open_shop$"))

        # 1️⃣0️⃣ Navigation Handlers
        app.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_to_previous$"))
        app.add_handler(CallbackQueryHandler(handle_back_to_country_menu, pattern="^back_to_country_menu$"))



        # Add specific handler for rp_channels
        from callback_handlers import show_channels_with_keyboard
        app.add_handler(CallbackQueryHandler(
            lambda update, context: show_channels_with_keyboard(update.callback_query),
            pattern="^rp_channels$"
        ))

        # Shop pagination handlers
        app.add_handler(CallbackQueryHandler(show_shop_category, pattern="^shop_category_"))
        app.add_handler(CallbackQueryHandler(show_shop_items_page, pattern="^shop_page_"))
        app.add_handler(CallbackQueryHandler(handle_item_purchase, pattern="^buy_item_"))
        app.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_purchase$"))
        app.add_handler(CallbackQueryHandler(admin_lock_shop, pattern="^admin_lock_shop$"))
        app.add_handler(CallbackQueryHandler(toggle_block_country, pattern=r"^toggle_block_country:"))

        app.add_handler(CallbackQueryHandler(show_admin_shop_page, pattern="^admin_shop_page_"))


        # 1️⃣1️⃣ General Main Menu Handler (LAST)
        app.add_handler(CallbackQueryHandler(handle_main_menu))

        # Message handlers
        app.add_handler(MessageHandler(pv_filter & filters.PHOTO, handle_photo_router))
        app.add_handler(MessageHandler(pv_filter & filters.TEXT & (~filters.COMMAND), handle_text_router))

        # Admin shop image handlers
        app.add_handler(MessageHandler(filters.PHOTO, handle_shop_item_image))
        app.add_handler(MessageHandler(filters.PHOTO, handle_new_shop_image))

        app.add_error_handler(error_handler)

        # Add job queue if available
        if hasattr(app, 'job_queue') and app.job_queue:
            app.job_queue.run_repeating(scheduled_cleanup, interval=300, first=10)

        return app
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise


logging.basicConfig(level=logging.INFO)

# def main():
#     """Main function to start the bot using polling mode"""
#     try:
#         logger.info("🔄 Starting bot in polling mode...")
#         logger.info(f"🤖 Bot token configured: {'✅' if BOT_TOKEN else '❌'}")

#         if not BOT_TOKEN:
#             raise ValueError("BOT_TOKEN is not set")

#         # Create application
#         app = create_application()
        

#         # Start polling with optimized settings
#         app.run_polling(
#             allowed_updates=Update.ALL_TYPES,
#             drop_pending_updates=True,
#             close_loop=False
#         )

#     except Exception as e:
#         logger.error(f"Error starting bot: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)

# # Signal handler for graceful shutdown
# def signal_handler(sig, frame):
#     logger.info(f"\n🛑 Received signal {sig}, shutting down gracefully...")
#     sys.exit(0)

# if __name__ == "__main__":
#     # Set up signal handlers for graceful shutdown
#     signal.signal(signal.SIGINT, signal_handler)
#     signal.signal(signal.SIGTERM, signal_handler)

#     try:
#         logger.info("🚀 Starting Telegram bot...")
#         main()
#         asyncio.create_task(periodic_git_push())
#         # asyncio.run(start_bot_and_scheduler())
#     except KeyboardInterrupt:
#         logger.info("🛑 Bot stopped by user")
#     except SystemExit:
#         logger.info("🛑 Bot stopped gracefully") 
#     except Exception as e:
#         logger.error(f"❌ Failed to start bot: {e}")
#         import traceback
#         traceback.print_exc()
#         sys.exit(1)

async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)

        # اجرای پردازش آپدیت در پس‌زمینه
        asyncio.create_task(app.process_update(update))

        return web.Response(text="OK")
    except Exception:
        logging.exception("❌ Webhook handler error")
        return web.Response(status=503, text="Error")

async def root(request):
    return web.Response(text="Bot is alive!")

async def main():
    app = create_application()
    render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if not render_url:
        print("❌ RENDER_EXTERNAL_HOSTNAME is not set")
        return

    webhook_url = f"https://{render_url}/{BOT_TOKEN}"
    print(f"✅ Setting webhook to: {webhook_url}")
    await app.bot.set_webhook(url=webhook_url, max_connections=15)

    await app.initialize()
    await app.start()

    webapp = web.Application()
    webapp.router.add_post(f"/{BOT_TOKEN}", handle_webhook)
    webapp.router.add_get("/", root)
    webapp.router.add_get("/setwebhook", set_webhook_handler)

    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    print(f"🚀 Bot is running with webhook on port {PORT}")
    asyncio.create_task(periodic_git_push())
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
