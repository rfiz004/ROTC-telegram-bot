import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import manage_country_menu, back_and_home_buttons, news_type_menu, select_country_menu
from config import CHANNEL_ID, RP_PASSWORDS, COUNTRY_ADMINS
from utils import validate_user_input

with open("countries.json", encoding="utf-8") as f:
    COUNTRIES_AREAS = json.load(f).get("countries_areas", {})

logger = logging.getLogger(__name__)

# Global data variables
countries_data = {}
passwords_data = {}

def load_data():
    """Load countries and passwords data"""
    global countries_data, passwords_data
    try:
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)
        with open("passwords.json", "r", encoding="utf-8") as f:
            passwords_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        countries_data = {"countries_areas": {}}
        passwords_data = {"passwords": {}}

def load_passwords_data():
    """Load passwords from JSON file"""
    try:
        with open("passwords.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading passwords: {e}")
        return {"passwords": {}}

# Initial load
load_data()

async def open_manage_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open country management - either direct auth or country selection"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    try:
        # Check if user has admin session
        if user_data.get("admin_session"):
            admin_countries = user_data.get("admin_countries", [])
            if len(admin_countries) == 1:
                # Direct access for single country admin
                country = admin_countries[0]
                context.user_data[user_id].update({
                    "country": country,
                    "province": "admin",
                    "authenticated": True,
                    "flow_type": "country_management"
                })
                await query.edit_message_text("✅ خوش اومدی! چه کمکی میتونم بهت بکنم؟", reply_markup=manage_country_menu())
            else:
                # Multiple countries selection
                await query.edit_message_text(
                    "🌍 کشور مورد نظر برای مدیریت را انتخاب کنید:",
                    reply_markup=select_country_menu(admin_countries)
                )
        else:
            # Regular country selection flow
            try:
                passwords_data = load_passwords_data()
                countries = list(passwords_data["passwords"].keys())
            except:
                countries = list(countries_data["countries_areas"].keys())

            keyboard = []
            for country in countries:
                keyboard.append([InlineKeyboardButton(
                    f"🌍 {country}",
                    callback_data=f"manage_select_country_{country}"
                )])
            keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])

            await query.edit_message_text(
                "🌍 کشور خودتو انتخاب کن:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Error in open_manage_country: {e}")
        await query.edit_message_text("❌ خطا در بارگذاری منوی کشورها", reply_markup=back_and_home_buttons())

async def manage_select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country selection for management"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    try:
        country = query.data.replace("manage_select_country_", "")

        # Check if user has admin session from RP Settings
        if user_data.get("admin_session") and user_data.get("admin_role") == "multi_country_admin":
            admin_countries = user_data.get("admin_countries", [])
            if country.lower() in [c.lower() for c in admin_countries]:
                # Admin has access to this country, bypass province selection
                context.user_data[user_id].update({
                    "country": country,
                    "province": "admin",
                    "authenticated": True,
                    "flow_type": "country_management"
                })
                await query.edit_message_text("✅ خوش اومدی! چه کمکی میتونم بهت بکنم؟", reply_markup=manage_country_menu())
                return

        # Regular flow - require province selection and password
        context.user_data[user_id] = context.user_data.get(user_id, {})
        context.user_data[user_id].update({
            "selected_country_for_province": country,
            "flow_type": "country_management"
        })

        passwords_data = load_passwords_data()
        country_passwords = passwords_data["passwords"].get(country, {})
        provinces = list(country_passwords.keys())

        if not provinces:
            await query.edit_message_text(f"❌ هیچ استانی برای کشور {country} تعریف نشده")
            return

        # Create province selection keyboard
        keyboard = []
        for province in provinces:
            keyboard.append([InlineKeyboardButton(province, callback_data=f"province|{province}")])

        keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")])

        await query.edit_message_text(
            f"🏰 استان خود را در کشور {country} انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in manage_select_country: {e}")
        await query.edit_message_text("❌ خطا در انتخاب کشور", reply_markup=back_and_home_buttons())

async def select_country_province(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle province selection"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    try:
        # Parse callback data
        province = query.data.replace("province|", "")
        country = user_data.get("selected_country_for_province")

        if not country:
            await query.edit_message_text("❌ کشور انتخاب نشده")
            return

        # Set country management flow and store selection
        context.user_data[user_id].update({
            "selected_province": province,
            "state": "awaiting_password"
        })

        await query.edit_message_text(
            f"🔐 رمز عبور استان {province} در کشور {country} را وارد کنید:"
        )
    except Exception as e:
        logger.error(f"Error in select_country_province: {e}")
        await query.edit_message_text("❌ خطا در انتخاب استان", reply_markup=back_and_home_buttons())

# async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Check password for country access"""
#     user_id = update.message.from_user.id
#     password = update.message.text.strip()
#     user_data = context.user_data.get(user_id, {})

#     try:
#         province = user_data.get("selected_province")
#         country = user_data.get("selected_country_for_province")

#         if not province or not country:
#             await update.message.reply_text("❌ خطا در احراز هویت. لطفاً مجدداً تلاش کنید.")
#             return

#         passwords_data = load_passwords_data()
#         correct_password = passwords_data["passwords"].get(country, {}).get(province)

#         if password == correct_password:
#             context.user_data[user_id].update({
#                 "authenticated": True,
#                 "country": country,
#                 "province": province,
#                 "state": None,
#                 "flow_type": "country_management"
#             })
#             await update.message.reply_text("✅ خوش اومدی! چه کمکی میتونم بهت بکنم؟", reply_markup=manage_country_menu())
#         else:
#             await update.message.reply_text("❌ رمز عبور اشتباه است. دوباره تلاش کن:")
#     except Exception as e:
#         logger.error(f"Error checking password: {e}")
#         await update.message.reply_text("❌ خطا در احراز هویت")

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    password = update.message.text.strip()
    user_data = context.user_data.get(user_id, {})

    logger.info(f"[check_password] User ID: {user_id} وارد کرده رمز: '{password}'")

    try:
        province = user_data.get("selected_province", "").strip()
        country = user_data.get("selected_country_for_province", "").strip()

        logger.info(f"[check_password] کشور انتخابی: '{country}', استان انتخابی: '{province}'")

        if not province or not country:
            logger.warning("[check_password] خطا: کشور یا استان انتخاب نشده‌اند.")
            await update.message.reply_text("❌ خطا در احراز هویت. لطفاً مجدداً تلاش کنید.")
            return

        passwords_data = load_passwords_data()

        logger.debug(f"[check_password] داده‌های رمز: {passwords_data}")

        correct_password = passwords_data.get("passwords", {}).get(country, {}).get(province)

        logger.info(f"[check_password] رمز صحیح پیدا شده: '{correct_password}'")

        if correct_password is None:
            logger.warning(f"[check_password] رمز برای کشور '{country}' و استان '{province}' یافت نشد.")
            await update.message.reply_text("❌ خطا: رمز عبور برای این استان تعریف نشده است.")
            return

        if password.lower() == correct_password.lower():
            logger.info("[check_password] رمز عبور صحیح است.")
            context.user_data[user_id].update({
                "authenticated": True,
                "country": country,
                "province": province,
                "state": None,
                "flow_type": "country_management"
            })
            context.user_data[user_id]["selected_province"] = province
            await update.message.reply_text("✅ خوش اومدی! چه کمکی میتونم بهت بکنم؟", reply_markup=manage_country_menu())
        else:
            logger.warning("[check_password] رمز وارد شده اشتباه است.")
            await update.message.reply_text("❌ رمز عبور اشتباه است. دوباره تلاش کن:")

    except Exception as e:
        logger.error(f"Error checking password: {e}", exc_info=True)
        await update.message.reply_text("❌ خطا در احراز هویت")


async def handle_country_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle country menu operations"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    try:
        # Check authentication
        if not user_data.get("authenticated") and not user_data.get("admin_session"):
            await query.edit_message_text("ابتدا وارد سیستم کشور شوید.")
            return
        if query.data == "country_overview":
            # Show detailed province information
            try:
                from province_handler import show_province_info
                from callback_handlers import push_navigation_state
                push_navigation_state(user_data, "country_menu")
                await show_province_info(update, context)
            except ImportError:
                country = user_data.get("country", "نامشخص")
                province = user_data.get("province", "نامشخص")

                overview_text = f"""🏰 **نمایش استان {province}**
        🌍 کشور: {country}

        📊 وضعیت کلی:
        • جمعیت: نامشخص
        • اقتصاد: پایدار
        • امنیت: عالی

        💰 منابع موجود:
        • طلا: نامشخص
        • نقره: نامشخص
        • مس: نامشخص"""

                await query.edit_message_text(overview_text, reply_markup=back_and_home_buttons())
        elif query.data == "country_news":
            # News type selection
            await query.edit_message_text("📢 نوع اعلامیه را انتخاب کنید:", reply_markup=news_type_menu())

        elif query.data.startswith("news_"):
            news_type = query.data.replace("news_", "")
            context.user_data[user_id]["news_type"] = news_type
            context.user_data[user_id]["state"] = "awaiting_character_name"

            await query.edit_message_text("👤 نام کاراکتر خودت رو بنویس:")

        elif query.data == "open_shop":
            # Open shop menu
            try:
                from shop_handler import open_shop_menu
                await open_shop_menu(update, context)
            except ImportError:
                await query.edit_message_text("فروشگاه در حال حاضر در دسترس نیست.")

        elif query.data == "economy_overview":
            # Show detailed province information using the same logic as province_handler
            try:
                from province_handler import show_province_info
                from callback_handlers import push_navigation_state
                push_navigation_state(user_data, "country_menu")
                await show_province_info(update, context)
            except ImportError:
                # Fallback to basic economic display
                country = user_data.get("country", "نامشخص")
                province = user_data.get("province", "نامشخص")

                economy_text = f"""{country} : {province}

📊 وضعیت اقتصادی کلی:
• تولید ناخالص داخلی: پایدار
• نرخ بیکاری: پایین  
• تورم: کنترل‌شده

💎 منابع طبیعی:
• طلا: متوسط
• نقره: زیاد
• مس: کم
• آهن: متوسط"""

                await query.edit_message_text(economy_text, reply_markup=back_and_home_buttons())

        elif query.data == "transfer_menu":
            # Transfer menu
            try:
                from transfer_handler import show_transfer_menu
                await show_transfer_menu(update, context)
            except ImportError:
                await query.edit_message_text("سیستم انتقالات در حال حاضر در دسترس نیست.")
                
        elif query.data == "admin_change_tax":
            await show_change_tax_menu(update, context)
            
        elif query.data == "admin_change_population":
            await show_change_population_menu(update, context)
            
        elif query.data == "admin_change_popularity":
            await show_change_popularity_menu(update, context)
            
        else:
            await query.edit_message_text("گزینه نامعتبر", reply_markup=manage_country_menu())
    except Exception as e:
        logger.error(f"Error in handle_country_menu: {e}")
        await query.edit_message_text("❌ خطا در پردازش درخواست", reply_markup=back_and_home_buttons())

async def collect_character_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect character name for news"""
    user_id = update.message.from_user.id
    character_name = update.message.text.strip()

    try:
        context.user_data[user_id]["character_name"] = character_name
        context.user_data[user_id]["state"] = "awaiting_news_text"

        await update.message.reply_text("📝 حالا متن اعلامیه رو بنویس:")
    except Exception as e:
        logger.error(f"Error in collect_character_name: {e}")
        await update.message.reply_text("❌ خطا در ثبت نام کاراکتر")

# async def collect_news_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Collect and process news text"""
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     news_text = update.message.text

#     try:
#         character_name = user_data.get("character_name", "نامشخص")
#         country = user_data.get("country", "نامشخص")
#         province = user_data.get("province", "نامشخص")
#         news_type = user_data.get("news_type", "normal")

#         # Format message based on news type
#         if news_type == "war":
#             formatted_message = f"⚔️ **اعلام جنگ**\n\n📍 از: {country} - {province}\n👤 فرمانده: {character_name}\n\n{news_text}"
#         elif news_type == "sanction":
#             formatted_message = f"🚫 **اعلان تحریم**\n\n📍 از: {country} - {province}\n👤 مسئول: {character_name}\n\n{news_text}"
#         else:
#             formatted_message = f"📰 **اعلامیه رسمی**\n\n📍 از: {country} - {province}\n👤 منتشرکننده: {character_name}\n\n{news_text}"

#         # Send to channel if configured
#         try:
#             await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
#             success_msg = "✅ اعلامیه شما ارسال شد!"
#         except:
#             success_msg = f"✅ اعلامیه آماده شد:\n\n{formatted_message}"

#         await update.message.reply_text(success_msg, reply_markup=manage_country_menu())

#         # Clear state
#         context.user_data[user_id]["state"] = None
#         context.user_data[user_id]["step"] = None
#     except Exception as e:
#         logger.error(f"Error in collect_news_text: {e}")
#         await update.message.reply_text("❌ خطا در ارسال اعلامیه")

# async def collect_news_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     news_text = update.message.text.strip()

#     try:
#         sender_name = user_data.get("character_name", "نامشخص")
#         recipient_name = user_data.get("recipient_name", "نامشخص")  # فرض بر این که ذخیره شده
#         news_type = user_data.get("news_type", "normal")

#         # تعیین هشتگ بر اساس نوع اعلامیه
#         if news_type == "war":
#             hashtag = "#اعلام_جنگ"
#         elif news_type == "sanction":
#             hashtag = "#اعلام_تحریم"
#         else:
#             hashtag = "#News"

#         formatted_message = (
#             "──────⊱◈News◈⊰──────\n\n"
#             f"✦ Sender Name : {sender_name}\n"
#             f"✧ Recipient Name : {recipient_name}\n"
#             f"✦ News text : {news_text}\n\n"
#             f"{hashtag} \n\n"
#             "──────⊹⊱✫⊰⊹──────\n"
#             "https://t.me/R_O_T_C\n"
#             "https://t.me/R_O_T_C_News"
#         )

#         try:
#             await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
#             success_msg = "✅ اعلامیه شما ارسال شد!"
#         except Exception:
#             success_msg = f"✅ اعلامیه آماده شد:\n\n{formatted_message}"

#         await update.message.reply_text(success_msg, reply_markup=manage_country_menu())

#         context.user_data[user_id]["state"] = None
#         context.user_data[user_id]["step"] = None

#     except Exception as e:
#         logger.error(f"Error in collect_news_text: {e}")
#         await update.message.reply_text("❌ خطا در ارسال اعلامیه")

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

def news_country_menu():
    buttons = [
        [InlineKeyboardButton(country, callback_data=f"news_recipient:{country}")]
        for country in COUNTRIES
    ]
    return InlineKeyboardMarkup(buttons)

def news_province_menu(country):
    provinces = COUNTRIES_AREAS.get(country, [])
    buttons = [
        [InlineKeyboardButton(province, callback_data=f"news_province:{country}:{province}")]
        for province in provinces
    ]
    return InlineKeyboardMarkup(buttons)



# لیست کشورها که گفتی
COUNTRIES = list(COUNTRIES_AREAS.keys())

def _get_user_store(context, user_id):
    """
    بعضی پروژه‌ها context.user_data رو به صورت {user_id: {...}} نگه می‌دارن.
    این تابع این دو حالت رو پشتیبانی می‌کنه و مرجع دیکشنری مربوط به کاربر را برمی‌گردونه.
    """
    ud = context.user_data
    if isinstance(ud, dict) and user_id in ud and isinstance(ud[user_id], dict):
        return ud[user_id]
    return ud

# === اصلاح شده: دریافت متن اعلامیه ===
async def collect_news_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_store = _get_user_store(context, user_id)
    news_text = update.message.text.strip()

    try:
        sender_name = user_store.get("character_name", "نامشخص")
        recipient_name = user_store.get("recipient_name")  # ممکنه None باشه
        news_type = user_store.get("news_type", "normal")


        if not recipient_name:
            user_store["pending_news_text"] = news_text
            user_store["state"] = "waiting_for_recipient_from_news"
        
            await update.message.reply_text(
                "گیرنده مشخص نشده — یکی از کشورها را انتخاب کنید:",
                reply_markup=news_country_menu()
            )
            return


        # تعیین هشتگ بر اساس نوع اعلامیه
        if news_type == "war":
            hashtag = "#اعلام_جنگ"
        elif news_type == "sanction":
            hashtag = "#اعلام_تحریم"
        else:
            hashtag = "#News"

        formatted_message = (
            "──────⊱◈News◈⊰──────\n\n"
            f"✦ Sender Name : {sender_name} (@{query.from_user.username or query.from_user.full_name})\n"
            f"✧ Recipient Name : {recipient_name}\n"
            f"✦ News text : {news_text}\n\n"
            f"{hashtag} \n\n"
            "──────⊹⊱✫⊰⊹──────\n"
            "https://t.me/R_O_T_C\n"
            "https://t.me/R_O_T_C_News"
        )

        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
            success_msg = "✅ اعلامیه شما ارسال شد!"
        except Exception:
            # اگر ارسال به کانال ناموفق بود، حداقل پیش‌نمایش به کاربر نمایش داده شود
            success_msg = f"✅ اعلامیه آماده شد:\n\n{formatted_message}"

        await update.message.reply_text(success_msg, reply_markup=manage_country_menu())

        # پاک‌سازی حالت‌ها
        user_store.pop("pending_news_text", None)
        user_store["state"] = None
        user_store["step"] = None

    except Exception as e:
        logger.error(f"Error in collect_news_text: {e}")
        await update.message.reply_text("❌ خطا در ارسال اعلامیه")

# === handlerِ callback برای وقتی کاربر کشور را انتخاب می‌کند ===
# async def news_recipient_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     user_id = query.from_user.id
#     user_store = _get_user_store(context, user_id)

#     # انتظار داریم callback_data مثل "news_recipient:Aldemar" باشه
#     parts = query.data.split(":", 1)
#     if len(parts) != 2:
#         await query.message.reply_text("انتخاب نامعتبر. دوباره تلاش کنید.")
#         return

#     recipient_name = parts[1]
#     user_store["recipient_name"] = recipient_name

#     # اگر متن قبلاً ذخیره شده بود، اعلامیه رو کامل کن و ارسال کن
#     pending = user_store.pop("pending_news_text", None)

#     if pending:
#         sender_name = user_store.get("character_name", "نامشخص")
#         news_type = user_store.get("news_type", "normal")

#         if news_type == "war":
#             hashtag = "#اعلام_جنگ"
#         elif news_type == "sanction":
#             hashtag = "#اعلام_تحریم"
#         else:
#             hashtag = "#News"

#         formatted_message = (
#             "──────⊱◈News◈⊰──────\n\n"
#             f"✦ Sender Name : {sender_name}\n"
#             f"✧ Recipient Name : {recipient_name}\n"
#             f"✦ News text : {pending}\n\n"
#             f"{hashtag} \n\n"
#             "──────⊹⊱✫⊰⊹──────\n"
#             "https://t.me/R_O_T_C\n"
#             "https://t.me/R_O_T_C_News"
#         )

#         try:
#             await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
#             # حذف کیبورد قبلی (اگر می‌خوای)
#             try:
#                 await query.message.edit_reply_markup(reply_markup=None)
#             except Exception:
#                 pass
#             await query.message.reply_text("✅ اعلامیه شما ارسال شد!", reply_markup=manage_country_menu())
#         except Exception:
#             await query.message.reply_text(f"✅ اعلامیه آماده شد:\n\n{formatted_message}")
#     else:
#         # اگر متن ذخیره نشده بود، از کاربر می‌خوای متن رو بفرسته
#         user_store["state"] = "waiting_for_news_text"
#         await query.message.reply_text(f"گیرنده '{recipient_name}' انتخاب شد. حالا متن اعلامیه را ارسال کنید.")

async def news_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_store = _get_user_store(context, user_id)

    data = query.data

    if data.startswith("news_recipient:"):
        country = data.split(":", 1)[1]
        user_store["recipient_country"] = country

        # اگر گیرنده همون کشور خود کاربر بود، استان‌ها رو بفرست
        user_country = user_store.get("my_country")
        if country == user_country:
            user_store["state"] = "waiting_for_news_province"
            await query.message.edit_text(
                "📍 چون کشور گیرنده کشور خودتان است، لطفا استان را انتخاب کنید:",
                reply_markup=news_province_menu(country)
            )
        else:
            # اگر کشور متفاوت بود، اعلامیه رو ارسال کن (یا ادامه بده)
            user_store["recipient_name"] = country
            await send_news_announcement(update, context)

    elif data.startswith("news_province:"):
        _, country, province = data.split(":", 2)
        user_store["recipient_country"] = country
        user_store["recipient_province"] = province
        user_store["recipient_name"] = f"{province}, {country}"

        await send_news_announcement(update, context)

async def send_news_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    user_store = _get_user_store(context, user_id)

    sender_name = user_store.get("character_name", "نامشخص")
    recipient_name = user_store.get("recipient_name", "نامشخص")
    news_text = user_store.pop("pending_news_text", None)
    news_type = user_store.get("news_type", "normal")

    if news_text is None:
        user_store["state"] = "waiting_for_news_text"
        await update.callback_query.message.reply_text("لطفا ابتدا متن اعلامیه را ارسال کنید.")
        return

    if news_type == "war":
        hashtag = "#اعلام_جنگ"
    elif news_type == "sanction":
        hashtag = "#اعلام_تحریم"
    else:
        hashtag = "#News"

    formatted_message = (
        "──────⊱◈News◈⊰──────\n\n"
        f"✦ Sender Name : {sender_name}\n"
        f"✧ Recipient Name : {recipient_name}\n"
        f"✦ News text : {news_text}\n\n"
        f"{hashtag} \n\n"
        "──────⊹⊱✫⊰⊹──────\n"
        "https://t.me/R_O_T_C\n"
        "https://t.me/R_O_T_C_News"
    )

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=formatted_message)
        await update.callback_query.message.edit_reply_markup(reply_markup=None)
        await update.callback_query.message.reply_text("✅ اعلامیه شما ارسال شد!", reply_markup=manage_country_menu())
    except Exception:
        await update.callback_query.message.reply_text(f"✅ اعلامیه آماده شد:\n\n{formatted_message}")





async def show_change_tax_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current tax rate and prompt for new value"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    
    country = user_data.get("country")
    province = user_data.get("province")
    
    # Load current tax rate
    from province_handler import load_province_data
    province_data = load_province_data(country, province)
    current_tax = province_data.get("tax", 0)
    
    context.user_data[user_id]["state"] = "awaiting_tax_input"
    
    text = f"📈 تغییر نرخ مالیات\n\n"
    text += f"🏛️ استان: {province}\n"
    text += f"📊 نرخ مالیات فعلی: {current_tax}%\n\n"
    text += "💡 نرخ مالیات جدید را وارد کنید (0-100):"
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="country_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_change_population_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current population and prompt for new value"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    
    country = user_data.get("country")
    province = user_data.get("province")
    
    # Load current population
    from province_handler import load_province_data
    province_data = load_province_data(country, province)
    current_population = province_data.get("population", 0)
    
    context.user_data[user_id]["state"] = "awaiting_population_input"
    
    text = f"👥 تغییر جمعیت\n\n"
    text += f"🏛️ استان: {province}\n"
    text += f"📊 جمعیت فعلی: {current_population:,} نفر\n\n"
    text += "💡 جمعیت جدید را وارد کنید:"
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="country_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_change_popularity_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current popularity and prompt for new value"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    
    country = user_data.get("country")
    province = user_data.get("province")
    
    # Load current popularity
    from province_handler import load_province_data
    province_data = load_province_data(country, province)
    current_popularity = province_data.get("popularity", 0)
    
    context.user_data[user_id]["state"] = "awaiting_popularity_input"
    
    text = f"📊 تغییر محبوبیت\n\n"
    text += f"🏛️ استان: {province}\n"
    text += f"📊 محبوبیت فعلی: {current_popularity}/100\n\n"
    text += "💡 محبوبیت جدید را وارد کنید (0-100):"
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="country_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin input for tax, population, popularity"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    state = user_data.get("state")
    text_input = update.message.text.strip()
    
    country = user_data.get("country")
    province = user_data.get("province")
    
    from province_handler import load_province_data, save_province_data
    
    try:
        if state == "awaiting_tax_input":
            new_tax = int(text_input)
            if new_tax < 0 or new_tax > 100:
                await update.message.reply_text("❌ نرخ مالیات باید بین 0 تا 100 باشد.")
                return True
                
            province_data = load_province_data(country, province)
            old_tax = province_data.get("tax", 0)
            province_data["tax"] = new_tax
            save_province_data(country, province, province_data)
            
            await update.message.reply_text(
                f"✅ نرخ مالیات با موفقیت تغییر کرد!\n\n"
                f"قبلی: {old_tax}%\n"
                f"جدید: {new_tax}%",
                reply_markup=manage_country_menu()
            )
            
        elif state == "awaiting_population_input":
            new_population = int(text_input) 
            if new_population < 0:
                await update.message.reply_text("❌ جمعیت نمی‌تواند منفی باشد.")
                return True
                
            province_data = load_province_data(country, province)
            old_population = province_data.get("population", 0)
            province_data["population"] = new_population
            save_province_data(country, province, province_data)
            
            await update.message.reply_text(
                f"✅ جمعیت با موفقیت تغییر کرد!\n\n"
                f"قبلی: {old_population:,} نفر\n"
                f"جدید: {new_population:,} نفر",
                reply_markup=manage_country_menu()
            )
            
        elif state == "awaiting_popularity_input":
            new_popularity = int(text_input)
            if new_popularity < 0 or new_popularity > 100:
                await update.message.reply_text("❌ محبوبیت باید بین 0 تا 100 باشد.")
                return True
                
            province_data = load_province_data(country, province)
            old_popularity = province_data.get("popularity", 0)
            province_data["popularity"] = new_popularity
            save_province_data(country, province, province_data)
            
            await update.message.reply_text(
                f"✅ محبوبیت با موفقیت تغییر کرد!\n\n"
                f"قبلی: {old_popularity}/100\n"
                f"جدید: {new_popularity}/100",
                reply_markup=manage_country_menu()
            )
        else:
            return False
            
        # Clear state
        context.user_data[user_id]["state"] = None
        return True
        
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")
        return True
    except Exception as e:
        logger.error(f"Error handling admin input: {e}")
        await update.message.reply_text("❌ خطا در ذخیره اطلاعات")
        return True

async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route user text input in country management flow"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    user_state = user_data.get("state")
    flow_type = user_data.get("flow_type")

    logger.info(f"Country handler - User {user_id}: flow_type={flow_type}, state={user_state}")

    # Only handle if we're in country management flow
    if flow_type != "country_management":
        return

    try:
        if user_state == "awaiting_password":
            await check_password(update, context)
        elif user_state == "awaiting_character_name":
            await collect_character_name(update, context)
        elif user_state == "awaiting_news_text":
            await collect_news_text(update, context)
        elif user_state in ["awaiting_tax_input", "awaiting_population_input", "awaiting_popularity_input"]:
            return await handle_admin_input(update, context)
        else:
            await update.message.reply_text("لطفاً از منوی کشور استفاده کنید.")
    except Exception as e:
        logger.error(f"Error in handle_user_text: {e}")
        await update.message.reply_text("❌ خطا در پردازش پیام")
