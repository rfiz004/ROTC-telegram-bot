import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import main_menu, skill_management_keyboard, manage_food_menu
from config import RP_PASSWORDS, COUNTRY_ADMINS, BIO_ADMIN_ID
from data_manager import handle_grain_priority, handle_grain_percentage
from province_handler import show_grain_preview
logger = logging.getLogger(__name__)

# Import consolidated admin access function from utils
from utils import check_admin_access, push_navigation_state, pop_navigation_state, get_current_navigation_state

async def handle_first_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu navigation - first handler"""
    query = update.callback_query
    await query.answer()

    try:
        action = query.data

        if action == "register_bio":
            from bio_handler import start_bio_submission
            await start_bio_submission(update, context)
        elif action == "manage_country":
            from country_handler import open_manage_country
            await open_manage_country(update, context)
        elif action == "shop_menu":
            from shop_handler import open_shop_menu
            await open_shop_menu(update, context)
        elif action == "transfer_menu":
            from transfer_handler import show_transfer_menu
            await show_transfer_menu(update, context)
        elif action == "rp_settings":
            await show_rp_settings(update, context)
        elif action == "rp_channels":
            # Use the more reliable inline keyboard approach
            await show_channels_with_keyboard(query)
        elif action == "main_menu":
            await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
        else:
            await query.edit_message_text("گزینه نامعتبر", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error in handle_first_main_menu: {e}")
        await query.edit_message_text("خطایی رخ داد", reply_markup=main_menu())

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button navigation"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})
    previous_step = user_data.get("previous_step")

    try:
        if previous_step == "admin_menu":
            from admin_handler import show_admin_menu
            await show_admin_menu(update, context)
        elif previous_step == "country_jobs":
            from admin_handler import show_country_jobs
            await show_country_jobs(update, context)
        else:
            await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Error in back navigation: {e}")
        await query.edit_message_text("منوی اصلی:", reply_markup=main_menu())

def push_navigation_state(user_data, state):
    """Push navigation state for back button functionality"""
    if "navigation_stack" not in user_data:
        user_data["navigation_stack"] = []
    # Avoid duplicate states
    if not user_data["navigation_stack"] or user_data["navigation_stack"][-1] != state:
        user_data["navigation_stack"].append(state)

def pop_navigation_state(user_data):
    """Pop navigation state for back button functionality"""
    if "navigation_stack" not in user_data:
        user_data["navigation_stack"] = []
    if user_data["navigation_stack"]:
        return user_data["navigation_stack"].pop()
    return None

def get_current_navigation_state(user_data):
    """Get current navigation state without popping"""
    if "navigation_stack" not in user_data:
        user_data["navigation_stack"] = []
    if user_data["navigation_stack"]:
        return user_data["navigation_stack"][-1]
    return None

# async def handle_back_to_country_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle back to country menu"""
#     query = update.callback_query
#     await query.answer()

#     from keyboards import manage_country_menu
#     await query.edit_message_text("منوی مدیریت کشور:", reply_markup=manage_country_menu())

async def handle_back_to_country_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to country menu"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    province = user_data.get("selected_province")
    if not province:
        await query.edit_message_text("⛔ ابتدا استان انتخاب نشده یا داده‌ای موجود نیست.")
        return

    from keyboards import manage_country_menu
    await query.edit_message_text("منوی مدیریت کشور:", reply_markup=manage_country_menu(province))


async def show_rp_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show RP settings menu"""
    query = update.callback_query
    await query.answer()

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [InlineKeyboardButton("🔐 ورود ادمین", callback_data="admin_login")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
    ]

    await query.edit_message_text("⚙️ تنظیمات RP:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_skill_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skill type selection"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    skill_type = query.data.replace("skill_type_", "")

    context.user_data[user_id] = context.user_data.get(user_id, {})
    context.user_data[user_id].update({
        "skill_type": skill_type,
        "step": "awaiting_skill_name"
    })

    skill_type_text = "عادی" if skill_type == "normal" else "خاص"
    await query.edit_message_text(f"📝 نام مهارت {skill_type_text} جدید را وارد کنید:")


import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import (
    main_menu, bio_admin_menu, master_admin_menu, shop_admin_menu, 
    multi_country_admin_menu, manage_country_menu,
    back_and_home_buttons, skill_type_selection_keyboard
)
from config import RP_PASSWORDS, COUNTRY_ADMINS
from data_manager import load_data, save_data, skills_config
import logging

logger = logging.getLogger(__name__)

# Safe imports
try:
    from bio_handler import start_bio_submission
except ImportError:
    async def start_bio_submission(*args, **kwargs):
        await args[0].callback_query.edit_message_text("ثبت بیوگرافی در حال حاضر در دسترس نیست.")

try:
    from country_handler import open_manage_country
except ImportError:
    async def open_manage_country(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت کشور در حال حاضر در دسترس نیست.")

try:
    from admin_handler import show_admin_menu, show_admin_job_list, show_admin_skill_list
except ImportError:
    async def show_admin_menu(*args, **kwargs):
        await args[0].callback_query.edit_message_text("پنل ادمین در حال حاضر در دسترس نیست.")
    async def show_admin_job_list(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مشاغل در حال حاضر در دسترس نیست.")
    async def show_admin_skill_list(*args, **kwargs):
        await args[0].callback_query.edit_message_text("مدیریت مهارت‌ها در حال حاضر در دسترس نیست.")

# Duplicate function removed - using consolidated version from utils.py

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button presses"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data

    try:
        user_data = context.user_data.get(user_id, {})

        if callback_data == "submit_bio":
            push_navigation_state(user_data, "main_menu")
            await start_bio_submission(update, context)

        elif callback_data == "manage_country":
            push_navigation_state(user_data, "main_menu")
            await open_manage_country(update, context)

        elif callback_data == "admin_menu":
            # Check if user has entered RP password
            if not user_data.get("admin_access") and not user_data.get("admin_session"):
                push_navigation_state(user_data, "main_menu")
                await query.edit_message_text(
                    "🔐 کلمه عبور RP را وارد کنید:", 
                    reply_markup=back_and_home_buttons()
                )
                context.user_data[user_id] = context.user_data.get(user_id, {})
                context.user_data[user_id]["step"] = "awaiting_rp_password"
            else:
                push_navigation_state(user_data, "main_menu")
                await show_admin_menu(update, context)

        elif callback_data == "rp_channels":
            # Handle RP channels request
            await show_channels_with_keyboard(query)

        
        elif callback_data == "back_to_main":
            # Clear user state and go back to main menu
            if user_id in context.user_data:
                context.user_data[user_id].clear()
            await query.edit_message_text(
                "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                reply_markup=main_menu()
            )
        elif callback_data == "open_shop":
            from shop_handler import open_shop_menu
            await open_shop_menu(update, context)

        elif callback_data == "shop":
            try:
                push_navigation_state(user_data, "main_menu")
                from shop_handler import open_shop_menu
                await open_shop_menu(update, context)
            except ImportError:
                await query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")

        elif callback_data == "transfer_menu":
            try:
                push_navigation_state(user_data, "main_menu")
                from transfer_handler import show_transfer_menu
                await show_transfer_menu(update, context)
            except ImportError:
                await query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")

        # Admin menu options
        elif callback_data == "admin_jobs":
            push_navigation_state(user_data, "admin_menu")
            await show_admin_job_list(update, context)
        elif callback_data == "admin_skills":
            push_navigation_state(user_data, "admin_menu")
            await show_admin_skill_list(update, context)
        elif callback_data == "admin_pending_bios":
            try:
                push_navigation_state(user_data, "admin_menu")
                from admin_handler import show_pending_bios
                await show_pending_bios(update, context)
            except ImportError:
                await query.edit_message_text("بررسی بیوگرافی‌ها در حال حاضر در دسترس نیست.")

        # Province admin options
        elif callback_data == "admin_province_menu":
            try:
                push_navigation_state(user_data, "admin_menu")
                from admin_province_handler import show_admin_province_menu
                await show_admin_province_menu(update, context)
            except ImportError:
                await query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")

        # Economic status
        elif callback_data == "country_overview":
            try:
                push_navigation_state(user_data, "country_menu")
                from province_handler import show_province_info
                await show_province_info(update, context)
            except ImportError:
                await query.edit_message_text("نمایش اطلاعات استان در حال حاضر در دسترس نیست.")

        else:
            # Unknown callback - redirect to main menu
            await query.edit_message_text(
                "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                reply_markup=main_menu()
            )

    except Exception as e:
        logger.error(f"Error in main menu handler: {e}")
        await query.edit_message_text("خطایی رخ داد. لطفاً مجدداً تلاش کنید.", reply_markup=main_menu())

# Navigation functions moved to utils.py for consolidation

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back navigation with proper state tracking"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    try:
        previous_state = pop_navigation_state(user_data)

        if previous_state == "admin_menu":
            await show_admin_menu(update, context)
        elif previous_state == "country_menu":
            from keyboards import manage_country_menu
            await query.edit_message_text("✅ خوش اومدی! چه کمکی میتونم بهت بکنم؟", reply_markup=manage_country_menu())
        elif previous_state == "admin_skill_list":
            await show_admin_skill_list(update, context)
        elif previous_state == "shop_menu":
            try:
                from shop_handler import open_shop_menu
                await open_shop_menu(update, context)
            except ImportError:
                await query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")
        elif previous_state == "transfer_menu":
            try:
                from transfer_handler import show_transfer_menu
                await show_transfer_menu(update, context)
            except ImportError:
                await query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
        elif previous_state == "bio_submission":
            await start_bio_submission(update, context)
        elif previous_state == "admin_province_menu":
            try:
                from admin_province_handler import show_admin_province_menu
                await show_admin_province_menu(update, context)
            except ImportError:
                await query.edit_message_text("مدیریت استان‌ها در حال حاضر در دسترس نیست.")
        elif previous_state == "admin_manage_shop":
            try:
                from admin_province_handler import admin_manage_shop
                await admin_manage_shop(update, context)
            except ImportError:
                await query.edit_message_text("مدیریت فروشگاه در حال حاضر در دسترس نیست.")
        elif previous_state == "admin_view_all_provinces":
            try:
                from admin_province_handler import show_all_provinces
                await show_all_provinces(update, context)
            except ImportError:
                await query.edit_message_text("مشاهده استان‌ها در حال حاضر در دسترس نیست.")
        elif previous_state == "main_menu":
            # Clear user state and go back to main menu only if explicitly from main menu
            await query.edit_message_text(
                "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                reply_markup=main_menu()
            )
        elif previous_state:
            # For unhandled states, try to go back one more level
            fallback_state = pop_navigation_state(user_data)
            if fallback_state:
                user_data.setdefault("navigation_history", []).append(fallback_state)
                await handle_back_navigation(update, context)
            else:
                await query.edit_message_text(
                    "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                    reply_markup=main_menu()
                )
        else:
            # Only go to main menu if no navigation history exists at all
            await query.edit_message_text(
                "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                reply_markup=main_menu()
            )
    except Exception as e:
        logger.error(f"Error in back navigation: {e}")
        await query.edit_message_text("خطا در بازگشت", reply_markup=back_and_home_buttons())

async def handle_back_to_country_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to country menu navigation"""
    query = update.callback_query
    await query.answer()

    try:
        await query.edit_message_text("منوی کشور", reply_markup=manage_country_menu())
    except Exception as e:
        logger.error(f"Error in back to country menu: {e}")
        await query.edit_message_text("خطا در بازگشت به منوی کشور", reply_markup=main_menu())

async def handle_skill_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skill type selection"""
    try:
        query = update.callback_query
        await query.answer()

        skill_type = query.data.replace("skill_type_", "")
        user_id = query.from_user.id

        # Store skill type in user data
        if user_id not in context.user_data:
            context.user_data[user_id] = {}
        context.user_data[user_id]["skill_type"] = skill_type

        # Handle based on skill type
        if skill_type == "normal":
            await query.edit_message_text(
                "📘 مهارت‌های عادی انتخاب شد.\nنام مهارت جدید را وارد کنید:",
                reply_markup=back_and_home_buttons()
            )
            context.user_data[user_id]["step"] = "awaiting_skill_name"
        elif skill_type == "special":
            await query.edit_message_text(
                "💠 مهارت‌های خاص انتخاب شد.\nنام مهارت جدید را وارد کنید:",
                reply_markup=back_and_home_buttons()
            )
            context.user_data[user_id]["step"] = "awaiting_skill_name"
        else:
            await query.edit_message_text(
                "❌ نوع مهارت نامعتبر است.",
                reply_markup=back_and_home_buttons()
            )
    except Exception as e:
        logger.error(f"Error in handle_skill_type_selection: {e}")
        try:
            await update.callback_query.edit_message_text(
                "خطایی رخ داد. لطفاً مجدداً تلاش کنید.",
                reply_markup=back_and_home_buttons()
            )
        except:
            pass

async def handle_province_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle province selection from inline keyboard"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    if query.data.startswith("select_province_"):
        province = query.data.replace("select_province_", "").replace("_", " ").strip()
        context.user_data[user_id]["province"] = province
        context.user_data[user_id]["province_name"] = province  # Store normalized province name

        logger.debug(f"Province selected: '{province}' for user {user_id}")

async def handle_back_to_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to previous menu functionality"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    # Get previous state from navigation stack
    previous_state = pop_navigation_state(user_data)

    if previous_state:
        logger.debug(f"Navigating back to: {previous_state}")

        # Route to appropriate handler based on state
        if previous_state == "main_menu":
            from message_handlers import show_main_menu
            await show_main_menu(update, context)
        elif previous_state == "country_menu":
            from country_handler import show_country_menu
            await show_country_menu(update, context)
        elif previous_state == "province_menu":
            from province_handler import show_province_menu
            await show_province_menu(update, context)
        elif previous_state == "admin_province_menu":
            await show_admin_province_menu(update, context)
        elif previous_state == "admin_view_all_provinces":
            await show_all_provinces(update, context)
        else:
            logger.warning(f"Unknown navigation state: {previous_state}")
            # Default fallback to main menu
            from message_handlers import show_main_menu
            await show_main_menu(update, context)
    else:
        # No previous state, go to main menu
        logger.debug("No previous state found, going to main menu")
        from message_handlers import show_main_menu
        await show_main_menu(update, context)



async def show_channels_with_keyboard(query):
    """Show channels using inline keyboard buttons - better UX alternative"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("🔷 کانال اصلی", url="https://t.me/R_O_T_C")],
        [InlineKeyboardButton("🧬 کانال بیوگرافی شخصیت‌ها", url="https://t.me/R_O_T_C_Bio")],
        [InlineKeyboardButton("📰 اخبار و اطلاعیه‌های رول", url="https://t.me/R_O_T_C_News")],
        [InlineKeyboardButton("🎭 میم‌ها و لحظات فان", url="https://t.me/R_O_T_C_Memes")],
        [InlineKeyboardButton("🛒 شاپ و فروشگاه رول", url="https://t.me/R_O_T_C_Shop")],
        [InlineKeyboardButton("🛒 بانک رول", url="https://t.me/R_O_T_C_Bank")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
    ]
    
    try:
        await query.edit_message_text(
            "📢 چنل‌های آرپی:\n\nبرای مشاهده هر کانال، روی دکمه مربوطه کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error showing channels keyboard: {e}")
        # Fallback to plain text if keyboard fails
        try:
            await query.edit_message_text(
                "📢 چنل‌های آرپی:\n\n"
                "🔷 کانال اصلی: @R_O_T_C\n"
                "🧬 کانال بیوگرافی: @R_O_T_C_Bio\n"
                "📰 اخبار و اطلاعیه‌ها: @R_O_T_C_News\n"
                "🎭 میم‌ها و لحظات فان: @R_O_T_C_Memes\n"
                "🛒 شاپ و فروشگاه: @R_O_T_C_Shop\n"
                "🛒 بانک رول: @R_O_T_C_Bank",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")
                ]])
            )
        except Exception as fallback_error:
            logger.error(f"Error in fallback channels display: {fallback_error}")
            await query.answer("خطا در نمایش لیست کانال‌ها")


SET_PRIORITY, SET_PERCENTAGE = range(2)
import logging
logger = logging.getLogger(__name__)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# async def food_handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     data = query.data
#     user_id = update.effective_user.id

#     logger.info(f"Callback data received: {data} from user {user_id}")

#     if user_id not in context.user_data:
#         context.user_data[user_id] = {}

#     if data == "set_grain_priority":
#         context.user_data[user_id]["step"] = "awaiting_grain_priority"
#         context.user_data[user_id]["flow_type"] = "grain_management"
#         await query.edit_message_text(
#             "📋 لطفاً اولویت غلات را به این شکل وارد کن:\n\n"
#             "`گوشت،مرغ،میوه`\n\n"
#             "✅ فقط از میان موارد زیر انتخاب کن:\n"
#             "گوشت، گندم، ماهی، مرغ، میوه",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ])
#         )

#     elif data == "set_grain_consumption":
#         context.user_data[user_id]["step"] = "awaiting_grain_percentage"
#         context.user_data[user_id]["flow_type"] = "grain_management"
#         await query.edit_message_text(
#             "⚙️ لطفاً درصد مصرف هر غله را وارد کن:\n\n"
#             "`گوشت=100،مرغ=50`\n\n"
#             "✅ درصد باید مضرب 50 و بدون مقدار منفی باشه.\n"
#             "❗ فقط غلاتی که توی اولویت نوشتی رو می‌تونی تنظیم کنی.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ])
#         )

#     elif data == "preview_grain_effect":
#         await show_grain_preview(update, context)  # اگر این تابع پیام یا کیبورد داره، باید توش هم دکمه بازگشت بذاری

#     elif data == "manage_food_menu":
#         logger.info(f"Grain menu opened for user {user_id} - selected_province: {context.user_data.get(user_id, {}).get('selected_province')}")
#         await query.edit_message_text(
#             "🍞 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
#             reply_markup=manage_food_menu()
#         )


async def food_handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    logger.info(f"Callback data received: {data} from user {user_id}")

    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    if data == "set_grain_priority":
        context.user_data[user_id]["step"] = "awaiting_grain_priority"
        context.user_data[user_id]["flow_type"] = "grain_management"
        await query.edit_message_text(
            "📋 لطفاً اولویت غلات را به این شکل وارد کن:\n\n"
            "`گوشت،مرغ،میوه`\n\n"
            "✅ فقط از میان موارد زیر انتخاب کن:\n"
            "گوشت، گندم، ماهی، مرغ، میوه",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )

    elif data == "set_grain_consumption":
        context.user_data[user_id]["step"] = "awaiting_grain_percentage"
        context.user_data[user_id]["flow_type"] = "grain_management"
        await query.edit_message_text(
            "⚙️ لطفاً درصد مصرف غلات را وارد کن (برای همه‌ی غلات به طور کلی):\n\n"
            "`مثال: 100`\n\n"
            "✅ درصد باید مضرب 50 و بدون مقدار منفی باشه.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )

    elif data == "preview_grain_effect":
        await show_grain_preview(update, context)  # اگر این تابع پیام یا کیبورد داره، باید توش هم دکمه بازگشت بذاری

    elif data == "manage_food_menu":
        logger.info(f"Grain menu opened for user {user_id} - selected_province: {context.user_data.get(user_id, {}).get('selected_province')}")
        await query.edit_message_text(
            "🍞 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=manage_food_menu()
        )
