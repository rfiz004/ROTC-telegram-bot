# --- Built-in modules ---
import asyncio
import logging
import os
import signal
import subprocess
import sys
import traceback
import secrets
import requests
import ipaddress

TELEGRAM_IPS = [
    "149.154.160.0/20",
    "91.108.4.0/22",
]
TELEGRAM_IPV6 = [
    "2001:67c:4e8::/48",
    "2001:b28:f23d::/48",
    "2001:b28:f23f::/48"
]

UPTIMEROBOT_IPS = [
    "3.12.251.153","3.20.63.178","3.77.67.4","3.79.134.69",
    "3.105.133.239","3.105.190.221","3.133.226.214","3.149.57.90",
    "3.212.128.62","5.161.61.238","5.161.73.160","5.161.75.7",
    "5.161.113.195","5.161.117.52","5.161.177.47","5.161.194.92",
    "5.161.215.244","5.223.43.32","5.223.53.147","5.223.57.22",
    "18.116.205.62","18.180.208.214","18.192.166.72","18.193.252.127",
    "24.144.78.39","24.144.78.185","34.198.201.66","45.55.123.175",
    "45.55.127.146","49.13.24.81","49.13.130.29","49.13.134.145",
    "49.13.164.148","49.13.167.123","52.15.147.27","52.22.236.30",
    "52.28.162.93","52.59.43.236","52.87.72.16","54.64.67.106",
    "54.79.28.129","54.87.112.51","54.167.223.174","54.249.170.27",
    "63.178.84.147","64.225.81.248","64.225.82.147","69.162.124.227",
    "69.162.124.235","69.162.124.238","78.46.190.63","78.46.215.1",
    "78.47.98.55","78.47.173.76","88.99.80.227","91.99.101.207",
    "128.140.41.193","128.140.106.114","129.212.132.140","134.199.240.137",
    "138.197.53.117","138.197.53.138","138.197.54.143","138.197.54.247",
    "138.197.63.92","139.59.50.44","142.132.180.39","143.198.249.237",
    "143.198.250.89","143.244.196.21","143.244.196.211","143.244.221.177",
    "144.126.251.21","146.190.9.187","152.42.149.135","157.90.155.240",
    "157.90.156.63","159.69.158.189","159.223.243.219","161.35.247.201",
    "167.99.18.52","167.235.143.113","168.119.53.160","168.119.96.239",
    "168.119.123.75","170.64.250.64","170.64.250.132","170.64.250.235",
    "178.156.181.172","178.156.184.20","178.156.185.127","178.156.185.231",
    "178.156.187.238","178.156.189.113","178.156.189.249","188.166.201.79",
    "206.189.241.133","209.38.49.1","209.38.49.206","209.38.49.226",
    "209.38.51.43","209.38.53.7","209.38.124.252","216.144.248.18",
    "216.144.248.19","216.144.248.21","216.144.248.22","216.144.248.23",
    "216.144.248.24","216.144.248.25","216.144.248.26","216.144.248.27",
    "216.144.248.28","216.144.248.29","216.144.248.30","216.245.221.83",
    "2a01:4f8:1c1a:3d53::1","2a01:4f8:1c1b:4ef4::1","2a01:4f8:1c1b:5b5a::1",
    "2a01:4f8:1c1b:7ecc::1","2a01:4f8:1c1c:11aa::1","2a01:4f8:1c1c:5353::1",
    "2a01:4f8:1c1c:7240::1","2a01:4f8:1c1c:a98a::1","2a01:4f8:c0c:83fa::1",
    "2a01:4f8:c2c:9fc6::1","2a01:4f8:c2c:beae::1","2a01:4f8:c012:c60e::1",
    "2a01:4f8:c013:3b0f::1","2a01:4f8:c013:3c52::1","2a01:4f8:c013:3c53::1",
    "2a01:4f8:c013:3c54::1","2a01:4f8:c013:3c55::1","2a01:4f8:c013:3c56::1",
    "2a01:4f8:c013:34c0::1","2a01:4f8:c013:c18::1","2a01:4f8:c17:42e4::1",
    "2a01:4ff:2f0:3b3a::1","2a01:4ff:2f0:27de::1","2a01:4ff:2f0:193c::1",
    "2a01:4ff:f0:3e03::1","2a01:4ff:f0:5f80::1","2a01:4ff:f0:7fad::1",
    "2a01:4ff:f0:9c5f::1","2a01:4ff:f0:2219::1","2a01:4ff:f0:b2f2::1",
    "2a01:4ff:f0:b6f1::1","2a01:4ff:f0:bfd::1","2a01:4ff:f0:d3cd::1",
    "2a01:4ff:f0:d283::1","2a01:4ff:f0:e9cf::1","2a01:4ff:f0:e516::1",
    "2a01:4ff:f0:eccb::1","2a01:4ff:f0:efd1::1","2a01:4ff:f0:fdc7::1",
    "2a03:b0c0:2:f0::bd91:f001","2a03:b0c0:2:f0::bd92:1","2a03:b0c0:2:f0::bd92:1001",
    "2a03:b0c0:2:f0::bd92:2001","2a03:b0c0:2:f0::bd92:4001","2a03:b0c0:2:f0::bd92:5001",
    "2a03:b0c0:2:f0::bd92:6001","2a03:b0c0:2:f0::bd92:7001","2a03:b0c0:2:f0::bd92:8001",
    "2a03:b0c0:2:f0::bd92:9001","2a03:b0c0:2:f0::bd92:a001","2a03:b0c0:2:f0::bd92:b001",
    "2a03:b0c0:2:f0::bd92:c001","2a03:b0c0:2:f0::bd92:e001","2a03:b0c0:2:f0::bd92:f001",
    "2a05:d014:1815:3400:6d:9235:c1c0:96ad","2a05:d014:1815:3400:90b4:4ef9:5631:b170",
    "2a05:d014:1815:3400:654f:bd37:724c:212b","2a05:d014:1815:3400:9779:d8e9:100a:9642",
    "2a05:d014:1815:3400:af29:e95e:64ff:df81","2a05:d014:1815:3400:c7d6:f7f3:6cc1:30d1",
    "2a05:d014:1815:3400:d784:e5dd:8e0:67cb","2400:6180:10:200::56a0:b000","2400:6180:10:200::56a0:c000",
    "2400:6180:10:200::56a0:e000","2400:6180:100:d0::94b6:4001","2400:6180:100:d0::94b6:5001",
    "2400:6180:100:d0::94b6:7001","2406:da1c:9c8:dc02:7ae1:f2ea:ab91:2fde","2406:da1c:9c8:dc02:7db9:f38b:7b9f:402e",
    "2406:da1c:9c8:dc02:82b2:f0fd:ee96:579","2406:da14:94d:8601:9d0d:7754:bedf:e4f5","2406:da14:94d:8601:b325:ff58:2bba:7934",
    "2406:da14:94d:8601:db4b:c5ac:2cbe:9a79","2600:1f16:775:3a00:3f24:5bb0:95d7:5a6b","2600:1f16:775:3a00:8c2c:2ba6:778f:5be5",
    "2600:1f16:775:3a00:37bf:6026:e54a:f03a","2600:1f16:775:3a00:91ac:3120:ff38:92b5","2600:1f16:775:3a00:ac3:c5eb:7081:942e",
    "2600:1f16:775:3a00:dbbe:36b0:3c45:da32","2600:1f18:179:f900:4b7d:d1cc:2d10:211","2600:1f18:179:f900:5c68:91b6:5d75:5d7",
    "2600:1f18:179:f900:71:af9a:ade7:d772","2600:1f18:179:f900:2406:9399:4ae6:c5d3","2600:1f18:179:f900:4696:7729:7bb3:f52f",
    "2600:1f18:179:f900:e8dd:eed1:a6c:183b","2604:a880:800:14:0:1:68ba:d000","2604:a880:800:14:0:1:68ba:e000",
    "2604:a880:800:14:0:1:68bb:0","2604:a880:800:14:0:1:68bb:1000","2604:a880:800:14:0:1:68bb:3000",
    "2604:a880:800:14:0:1:68bb:4000","2604:a880:800:14:0:1:68bb:5000","2604:a880:800:14:0:1:68bb:6000",
    "2604:a880:800:14:0:1:68bb:7000","2604:a880:800:14:0:1:68bb:a000","2604:a880:800:14:0:1:68bb:b000",
    "2604:a880:800:14:0:1:68bb:c000","2604:a880:800:14:0:1:68bb:d000","2604:a880:800:14:0:1:68bb:e000",
    "2604:a880:800:14:0:1:68bb:f000","2607:ff68:107::4","2607:ff68:107::14","2607:ff68:107::33",
    "2607:ff68:107::48","2607:ff68:107::49","2607:ff68:107::50","2607:ff68:107::51",
    "2607:ff68:107::52","2607:ff68:107::53","2607:ff68:107::54","2607:ff68:107::55",
    "2607:ff68:107::56","2607:ff68:107::57","2607:ff68:107::58","2607:ff68:107::59",
    "2607:ff68:107::60"
]


# گرفتن IPهای UptimeRobot به‌صورت خودکار
# ترکیب همه IPها
ALL_ALLOWED_IPS = TELEGRAM_IPS + TELEGRAM_IPV6 + UPTIMEROBOT_IPS

# -------------------------
# تابع چک کردن IP در شبکه‌ها
def is_ip_in_networks(ip, networks):
    try:
        ip_addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(ip_addr in ipaddress.ip_network(net) for net in networks)

# -------------------------
# گرفتن IP واقعی کلاینت
def get_real_ip(request):
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote or ""


# --- Third-party modules ---
from aiohttp import web
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, Application
)
from telegram.error import Conflict, NetworkError, TelegramError

# --- Project modules ---
from config import BOT_TOKEN, PORT, GITHUB_REPO, GITHUB_TOKEN, GITHUB_BRANCH
from data_manager import (
    clear_expired_reservations, jobs_by_country, load_data_file,
    save_data_file, save_bios
)
from keyboards import main_menu
from callback_handlers import (
    handle_main_menu, handle_back_navigation,
    handle_back_to_country_menu, food_handle_callback,
    handle_skill_type_selection, show_channels_with_keyboard
)
from message_handlers import handle_all_messages
from run_git_push import run_git_push
from auto_commit_push import schedule_auto_push

# Handlers
from bio_handler import (
    select_job, ask_bio_fields, handle_skill_navigation,
    handle_skill_reset, handle_skill_continue, handle_skill_selection,
    collect_bio, handle_job_locks, start_bio_submission
)

from admin_handler import (
    show_admin_menu, show_admin_job_list, show_admin_skill_list,
    show_country_jobs, handle_job_actions, handle_skill_actions,
    handle_bio_approval, show_pending_bios, handle_admin_text_message,
    cleanup_incomplete_bio_for_user
)

from admin_province_handler import (
    show_admin_province_menu, show_all_provinces, view_province_admin,
    admin_manage_transfers, approve_transfer, reject_transfer,
    admin_manage_shop, admin_add_shop_item_prompt,
    handle_shop_item_text_input, handle_shop_item_image,
    show_country_admin_menu, show_country_provinces, show_country_transfers,
    admin_edit_shop_item, admin_delete_shop_item, confirm_delete_shop_item,
    handle_shop_edit_choice, show_admin_shop_page, handle_new_shop_caption,
    handle_new_shop_image, show_weekly_processing_menu,
    preview_weekly_processing, run_weekly_processing,
    admin_show_economy_overview, handle_province_edit, admin_view_shop_items,
    run_food_processing, back_to_admin_menu, admin_lock_shop, toggle_block_country
)

from country_handler import (
    check_password, handle_country_menu, collect_character_name,
    collect_news_text, select_country_province, handle_user_text,
    manage_select_country, open_manage_country, news_callback_handler
)

from shop_handler import (
    open_shop_menu, show_shop_category, show_shop_items_page,
    handle_item_purchase, confirm_purchase, handle_quantity_input,
    handle_shop_buy
)

from transfer_handler import (
    show_transfer_menu, show_domestic_transfer, show_international_transfer,
    show_transfer_items, show_transfer_category_items,
    handle_transfer_quantity, process_transfer_request, view_pending_transfers
)

from province_handler import (
    show_grain_preview, edit_tax_callback, handle_tax_input
)
from run_git_push import run_git_push

async def periodic_git_push():
    while True:
        logger.info("🔄 Running scheduled git push...")
        # await asyncio.get_running_loop().run_in_executor(None, run_git_push())
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_git_push)
        await asyncio.sleep(5 * 60)


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
        elif step in ["awaiting_shop_item_name", "awaiting_shop_item_type", "awaiting_shop_item_country",
              "awaiting_shop_item_description", "awaiting_shop_item_count", "awaiting_shop_item_price",
              "awaiting_shop_item_owner","awaiting_shop_item_hashtags"]:
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

# ────────────── Logging
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        await cleanup_incomplete_bio_for_user(update, context)

        if user_id in context.user_data:
            context.user_data[user_id].clear()
        
        await update.message.reply_text(
            "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
            reply_markup=main_menu()
        )

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        try:
            await update.message.reply_text("خطایی رخ داد. دوباره تلاش کن.")
        except:
            pass

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

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            f"🆔 آیدی این چت: `{update.effective_chat.id}`", 
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in get_chat_id: {e}")

# ────────────── Scheduled Jobs
async def scheduled_cleanup(context: ContextTypes.DEFAULT_TYPE):
    try:
        from timer_manager import should_run_task, update_task_time
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
        logger.warning("Another bot instance is running. Stopping this one...")
        await app.stop()
    elif isinstance(context.error, NetworkError):
        logger.warning(f"Network error: {context.error}")
    elif isinstance(context.error, TelegramError):
        logger.error(f"Telegram API error: {context.error}")
    else:
        logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

# ────────────── Build Application
app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_chat_id))

# Callbacks & Message Handlers
app.add_handler(CallbackQueryHandler(admin_manage_transfers, pattern="^admin_manage_transfers$"))
app.add_handler(CallbackQueryHandler(handle_skill_navigation, pattern="^skill_page_"))
app.add_handler(CallbackQueryHandler(handle_skill_reset, pattern="^reset_skills$"))
app.add_handler(CallbackQueryHandler(handle_skill_continue, pattern="^skills_done$"))
app.add_handler(CallbackQueryHandler(handle_skill_selection, pattern="^select_skill_"))
app.add_handler(CallbackQueryHandler(handle_job_locks, pattern="^job_locked$|^job_taken$|^job_azure_locked$"))
app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^bio_job_"))
app.add_handler(CallbackQueryHandler(select_job, pattern="^select_bio_country_"))
app.add_handler(CallbackQueryHandler(view_pending_transfers, pattern="^view_pending_transfers$"))
app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(approve|reject)_bio_"))
app.add_handler(CallbackQueryHandler(handle_skill_actions, pattern="^(add|remove)_skill$"))
app.add_handler(CallbackQueryHandler(back_to_admin_menu, pattern="^back_to_admin_menu$"))
app.add_handler(CallbackQueryHandler(run_food_processing, pattern="^run_food_processing$"))
app.add_handler(CallbackQueryHandler(food_handle_callback, pattern="^(set_grain_priority|set_grain_consumption|preview_grain_effect|manage_food_menu)$"))
app.add_handler(CallbackQueryHandler(handle_skill_type_selection, pattern="^skill_type_"))
app.add_handler(CallbackQueryHandler(show_country_admin_menu, pattern="^admin_country_menu_"))
app.add_handler(CallbackQueryHandler(show_country_provinces, pattern="^admin_country_provinces_"))
app.add_handler(CallbackQueryHandler(show_country_transfers, pattern="^admin_country_transfers_"))
app.add_handler(CallbackQueryHandler(edit_tax_callback, pattern="^edit_tax$"))
app.add_handler(CallbackQueryHandler(news_callback_handler, pattern="^(news_recipient:|news_province:)"))
app.add_handler(CallbackQueryHandler(show_admin_province_menu, pattern="^admin_province_menu$"))
app.add_handler(CallbackQueryHandler(admin_view_shop_items, pattern="^admin_view_shop_items$"))
app.add_handler(CallbackQueryHandler(show_grain_preview, pattern="^preview_grain_effect$"))
app.add_handler(CallbackQueryHandler(show_all_provinces, pattern="^admin_view_all_provinces$"))
app.add_handler(CallbackQueryHandler(view_province_admin, pattern="^admin_view_province_"))
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
app.add_handler(CallbackQueryHandler(show_shop_category, pattern="^shop_category_"))
app.add_handler(CallbackQueryHandler(show_shop_items_page, pattern="^shop_page_"))
app.add_handler(CallbackQueryHandler(handle_item_purchase, pattern="^buy_item_"))
app.add_handler(CallbackQueryHandler(confirm_purchase, pattern="^confirm_purchase$"))
app.add_handler(CallbackQueryHandler(show_transfer_menu, pattern="^transfer_menu$"))
app.add_handler(CallbackQueryHandler(show_domestic_transfer, pattern="^transfer_domestic$"))
app.add_handler(CallbackQueryHandler(show_international_transfer, pattern="^transfer_international$"))
app.add_handler(CallbackQueryHandler(show_transfer_items, pattern="^(domestic|international)_target_"))
app.add_handler(CallbackQueryHandler(show_transfer_category_items, pattern="^transfer_category_"))
app.add_handler(CallbackQueryHandler(handle_transfer_quantity, pattern="^transfer_item_"))
app.add_handler(CallbackQueryHandler(process_transfer_request, pattern="^confirm_transfer_request$"))
app.add_handler(CallbackQueryHandler(manage_select_country, pattern="^manage_select_country_"))
app.add_handler(CallbackQueryHandler(select_country_province, pattern="^province\\|"))
app.add_handler(CallbackQueryHandler(handle_country_menu, pattern="^country_|^news_|^economy_"))
app.add_handler(CallbackQueryHandler(open_shop_menu, pattern="^open_shop_menu$"))
app.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_to_previous$"))
app.add_handler(CallbackQueryHandler(handle_back_to_country_menu, pattern="^back_to_country_menu$"))
app.add_handler(CallbackQueryHandler(lambda update, context: show_channels_with_keyboard(update.callback_query), pattern="^rp_channels$"))
app.add_handler(CallbackQueryHandler(admin_lock_shop, pattern="^admin_lock_shop$"))
app.add_handler(CallbackQueryHandler(toggle_block_country, pattern=r"^toggle_block_country:"))
app.add_handler(CallbackQueryHandler(show_admin_shop_page, pattern="^admin_shop_page_"))
app.add_handler(CallbackQueryHandler(handle_main_menu))

app.add_handler(MessageHandler(pv_filter & filters.PHOTO, handle_photo_router))
app.add_handler(MessageHandler(pv_filter & filters.TEXT & (~filters.COMMAND), handle_text_router))
app.add_handler(MessageHandler(filters.PHOTO, handle_shop_item_image))
app.add_handler(MessageHandler(filters.PHOTO, handle_new_shop_image))

app.add_error_handler(error_handler)

if hasattr(app, 'job_queue') and app.job_queue:
    app.job_queue.run_repeating(scheduled_cleanup, interval=1800, first=1800)

# ────────────── Webhook Functions
# async def set_webhook_handler(request):
#     render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
#     if not render_url:
#         return web.Response(text="Missing RENDER_EXTERNAL_HOSTNAME", status=500)

#     webhook_url = f"https://{render_url}/{BOT_TOKEN}"
#     await app.bot.set_webhook(url=webhook_url, max_connections=15)
#     return web.Response(text=f"Webhook set to {webhook_url}")

# async def handle_webhook(request):
#     try:
#         data = await request.json()
#         update = Update.de_json(data, app.bot)
#         asyncio.create_task(app.process_update(update))
#         return web.Response(text="OK")
#     except Exception:
#         logging.exception("❌ Webhook handler error")
#         return web.Response(status=503, text="Error")

# async def root(request):
#     return web.Response(text="Bot is alive!")

# # ────────────── Main
# async def main():
#     render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
#     if not render_url:
#         logger.error("❌ RENDER_EXTERNAL_HOSTNAME is not set")
#         return

#     webhook_url = f"https://{render_url}/{BOT_TOKEN}"
#     logger.info(f"✅ Setting webhook to: {webhook_url}")

#     await app.initialize()
#     await set_bot_commands(app)
#     await app.bot.set_webhook(url=webhook_url, max_connections=15)
#     await app.start()

#     webapp = web.Application()
#     webapp.router.add_post(f"/{BOT_TOKEN}", handle_webhook)
#     webapp.router.add_get("/", root)
#     webapp.router.add_get("/setwebhook", set_webhook_handler)

#     runner = web.AppRunner(webapp)
#     await runner.setup()
#     site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
#     await site.start()

#     # asyncio.create_task(auto_push_every_15_minutes())  # گیت پوش خودکار
#     asyncio.create_task(periodic_git_push())
    
#     logger.info(f"🚀 Bot is running with webhook on port {PORT}")
#     await asyncio.Event().wait()

# if __name__ == "__main__":
#     asyncio.run(main())



WEBHOOK_PATH = secrets.token_hex(32)  # ۶۴ کاراکتر تصادفی
SECRET_TOKEN = secrets.token_hex(16)  # توکن مخفی ۳۲ کاراکتری

logger = logging.getLogger(__name__)

async def set_webhook_handler(request):
    # فقط با کلید ادمین اجازه بدیم
    auth = request.query.get("auth")
    if auth != os.environ.get("ADMIN_KEY"):  # توی تنظیمات Render مقدار ADMIN_KEY رو ست کن
        return web.Response(status=403, text="Forbidden")

    render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if not render_url:
        return web.Response(text="Missing RENDER_EXTERNAL_HOSTNAME", status=500)

    webhook_url = f"https://{render_url}/{WEBHOOK_PATH}"
    await app.bot.set_webhook(
        url=webhook_url,
        max_connections=15,
        secret_token=SECRET_TOKEN
    )
    return web.Response(text=f"Webhook set to {webhook_url}")

async def handle_webhook(request):
    client_ip = get_real_ip(request)

    ALL_ALLOWED_IPS = TELEGRAM_IPS + TELEGRAM_IPV6 + UPTIMEROBOT_IPS

    if not is_ip_in_networks(client_ip, ALL_ALLOWED_IPS):
        logger.warning(f"❌ Request from non-allowed IP: {client_ip}")
        return web.Response(status=403, text="Forbidden")

    # چک توکن (می‌تونی بعداً فعالش کنی)
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET_TOKEN:
        logger.warning("❌ Invalid secret token in webhook request")
        return web.Response(status=403, text="Forbidden")

    try:
        data = await request.json()
        update = Update.de_json(data, app.bot)
        asyncio.create_task(app.process_update(update))
        return web.Response(text="OK")
    except Exception:
        logger.exception("❌ Webhook handler error")
        return web.Response(status=503, text="Error")

async def root(request):
    return web.Response(text="Bot is alive!")

async def main():
    render_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    if not render_url:
        logger.error("❌ RENDER_EXTERNAL_HOSTNAME is not set")
        return

    webhook_url = f"https://{render_url}/{WEBHOOK_PATH}"
    logger.info(f"✅ Setting webhook to: {webhook_url}")

    await app.initialize()
    await set_bot_commands(app)
    await app.bot.set_webhook(
        url=webhook_url,
        max_connections=15,
        secret_token=SECRET_TOKEN
    )
    await app.start()

    webapp = web.Application()
    webapp.router.add_post(f"/{WEBHOOK_PATH}", handle_webhook)
    webapp.router.add_get("/", root)
    webapp.router.add_get("/setwebhook", set_webhook_handler)

    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    asyncio.create_task(periodic_git_push())
    logger.info(f"🚀 Bot is running with webhook on port {PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
