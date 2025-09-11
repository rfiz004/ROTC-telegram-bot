import json
import os
import re
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from province_handler import load_province_data, save_province_data
from transfer_handler import load_pending_transfers, save_pending_transfers
from keyboards import admin_back_buttons
from config import BIO_ADMIN_ID, RP_PASSWORDS, SHOP_CHANNEL

logger = logging.getLogger(__name__)

ECONOMIC_FOLDER = "EconomicItems"
PROVINCE_FOLDER = "provinces"
COUNTRIES_FILE = "countries.json"
TRANSFERS_FILE = "pending_transfers.json"
TIMERS_FILE = "timers.json"


BASE_CONSUMPTION_RATES = {
    "گوشت": (300, 1),
    "گندم": (300, 1),
    "ماهی": (250, 1),
    "مرغ": (250, 1),
    "میوه": (200, 1)
}

async def show_admin_province_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin province management menu"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Import check_admin_access function
    from utils import check_admin_access

    if not check_admin_access(user_data, required_role="province_admin") and not check_admin_access(user_data, required_role="multi_country_admin"):
        await query.edit_message_text("❌ دسترسی غیرمجاز. این بخش فقط برای ادمین‌های استان است.")
        return

    text = "👑 مدیریت استان‌ها"

    keyboard = [
        [InlineKeyboardButton("🏰 مشاهده تمام استان‌ها", callback_data="admin_view_all_provinces")],
        [InlineKeyboardButton("🔄 مدیریت انتقالات", callback_data="admin_manage_fers")],
        [InlineKeyboardButton("🛍 مدیریت فروشگاه", callback_data="admin_manage_shop")],
        [InlineKeyboardButton("⏰ پردازش هفتگی", callback_data="show_weekly_menu")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # فرض می‌کنیم master_admin_menu در همان ماژول یا یک ماژول import-شده هست
        from keyboards import master_admin_menu  # مسیر را مطابق پروژه‌ات اصلاح کن

        # اگر پیام قابل ویرایش است، edit کن، در غیر این صورت یک پیام جدید بفرست
        try:
            await query.edit_message_text(
                "👑 منوی اصلی ادمین:",
                reply_markup=master_admin_menu()
            )
        except Exception:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="👑 منوی اصلی ادمین:",
                reply_markup=master_admin_menu()
            )
    except Exception as e:
        logger.exception(f"Error in back_to_admin_menu: {e}")
        # fallback ساده: اگر چیزی اشتباه شد، پیام ساده بفرست
        await query.edit_message_text("❌ خطا در بازگشت به منوی ادمین.")


async def back_to_master_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from keyboards import master_admin_menu
    try:
        await query.edit_message_text("👑 منوی اصلی ادمین:", reply_markup=master_admin_menu())
    except:
        await context.bot.send_message(chat_id=query.message.chat_id, text="👑 منوی اصلی ادمین:", reply_markup=master_admin_menu())

async def back_to_bio_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from keyboards import bio_admin_menu  # یا هر تابع منوی بیو که داری
    try:
        await query.edit_message_text("👑 منوی ادمین بیو:", reply_markup=bio_admin_menu())
    except:
        await context.bot.send_message(chat_id=query.message.chat_id, text="👑 منوی ادمین بیو:", reply_markup=bio_admin_menu())



async def show_all_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all provinces across all countries"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Import check_admin_access function  
    from callback_handlers import check_admin_access

    if not check_admin_access(user_data, required_role="multi_country_admin"):
        await query.edit_message_text("❌ دسترسی غیرمجاز.")
        return

    try:
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        text = "🏰 تمام استان‌ها:\n\n"
        keyboard = []

        for country, provinces in countries_data.get("countries_areas", {}).items():
            text += f"🌍 {country}:\n"
            for province in provinces:
                text += f"   • {province}\n"
                keyboard.append([InlineKeyboardButton(
                    f"📊 {country} - {province}", 
                    callback_data=f"admin_view_province_{country}_{province.replace(' ', '_')}"
                )])
            text += "\n"

        keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_province_menu")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Error in show_all_provinces: {e}")
        await query.edit_message_text("❌ خطا در نمایش استان‌ها")

def format_province_info(province_info):
    """Format province information for display"""
    def get(data, key, default=0):
        return data.get(key, default)

    def format_number(n):
        return f"{n:,}"

    text = f"{province_info.get('country')} : {province_info.get('province')}\n\n"

    # معادن with production info
    mines = province_info.get("mines", {})
    mine_productions = province_info.get("mine_productions", {})
    text += "⬤ معدن :\n"

    total_mine_income = 0
    for mine_name, count in mines.items():
        weekly_income_per_unit = mine_productions.get(mine_name, {}).get("weekly_per_unit", 0)
        total_weekly_income = count * weekly_income_per_unit
        total_mine_income += total_weekly_income

        if weekly_income_per_unit > 0:
            text += f"✧ {mine_name} : {format_number(count)} (درآمد هفتگی: {format_number(total_weekly_income)})\n"
        else:
            text += f"✧ {mine_name} : {format_number(count)}𓆩𐊧𓆪\n"

    if total_mine_income > 0:
        text += f"\n💰 کل درآمد هفتگی معادن: {format_number(total_mine_income)}\n"

    text += "\n"

    # ثروت، جمعیت، مالیات، محبوبیت
    text += f"⬤ ثروت : {format_number(get(province_info, 'wealth'))}𓆩𐊧𓆪\n"
    text += f"⬤ جمیعت : {format_number(get(province_info, 'population'))} نفر\n"
    text += f"⬤ مالیات : {get(province_info, 'tax')}\n"
    text += f"⬤ محبوبیت : {get(province_info, 'popularity')}\n\n"

    # ارتش
    army = province_info.get("army", {})
    # total_army = get(province_info, "total_army", sum(army.values()))
    total_army = sum(army.values())
    text += f"⬤ تعداد کل سرباز : {format_number(total_army)}\n"
    for unit in ["کماندار", "شمشیرزن", "نیزه دار", "سواره نظام"]:
        text += f"✧ {unit} : {format_number(army.get(unit, 0))}\n"
    text += "\n"

    # # قلعه
    # castle = province_info.get("castle", [])
    # text += "⬤ قلعه :\n"
    # if castle:
    #     for part in castle:
    #         text += f"✧ {part}\n"
    # else:
    #     text += "✧\n"
    # text += "\n"

    # # سازه‌ها، سلاح، متفرقه
    # for section in ["structures", "weapons", "misc"]:
    #     items = province_info.get(section, [])
    #     title = {
    #         "structures": "سازه ها",
    #         "weapons": "سلاح",
    #         "misc": "متفرقه"
    #     }[section]
    #     text += f"⬤ {title} :\n"
    #     if items:
    #         for item in items:
    #             text += f"✧ {item}\n"
    #     else:
    #         text += "✧\n"
    #     text += "\n"

    # قلعه
    castle = province_info.get("castle", {})
    text += "⬤ قلعه :\n"
    if castle:
        for part, count in castle.items():
            text += f"✧ {part} : {count}\n"
    else:
        text += "✧\n"
    text += "\n"
    
    # سازه‌ها، سلاح، متفرقه
    for section in ["structures", "weapons", "misc"]:
        items = province_info.get(section, {})
        title = {
            "structures": "سازه ها",
            "weapons": "سلاح",
            "misc": "متفرقه"
        }[section]
        text += f"⬤ {title} :\n"
        if items:
            for item, count in items.items():
                text += f"✧ {item} : {count}\n"
        else:
            text += "✧\n"
        text += "\n"


    # اقلام اقتصادی
    economic_items = province_info.get("economic_items", {})
    default_economic_keys = [
        "گندم", "گوشت", "ماهی", "مرغ", "میوه", "فولاد", "شیشه", "سنگ",
        "چوب", "جواهر", "پنبه", "پارچه", "چرم", "شراب"
    ]
    text += "⬤ اقلام اقتصادی:\n"
    for item in default_economic_keys:
        text += f"✧ {item} : {format_number(economic_items.get(item, 0))}\n"
    text += "\n"

    # Economic structures with production info
    eco_structs = province_info.get("economic_structures", {})
    text += "⬤ سازه‌های اقتصادی:\n\n"

    # Calculate weekly production for display
    weekly_production = {}
    for struct_name, struct_data in eco_structs.items():
        count = struct_data.get("count", 0)
        if count > 0:
            produces = struct_data.get("product", "")
            weekly_per_unit = struct_data.get("weekly_output", 0)
            total_weekly = count * weekly_per_unit

            if produces and weekly_per_unit > 0:
                text += f"✧ تعداد {struct_name} : {count} = {total_weekly} {produces} در هفته\n"
                weekly_production[produces] = weekly_production.get(produces, 0) + total_weekly
            else:
                text += f"✧ {struct_name} : {count}\n"


    # If no structures have count > 0, show a default message
    if not any(data.get("count", 0) > 0 for data in eco_structs.values()):
        text += "✧ هیچ سازه اقتصادی موجود نیست\n"


    # Show total weekly production summary
    if weekly_production:
        text += "\n📊 خلاصه تولید هفتگی:\n"
        for item, amount in weekly_production.items():
            text += f"   • {item}: +{amount:,}\n"

    return text


def normalize_structures(structs):
    # اگر از قبل دیکشنری است، همونو برگردون
    if isinstance(structs, dict):
        # مطمئن شو همه مقادیر int هستند
        return {str(k).strip(): int(v) for k, v in structs.items() if str(k).strip()}

    result = {}
    if isinstance(structs, list):
        for entry in structs:
            if isinstance(entry, str):
                s = entry.strip()
                # حالت "نام - تعداد" یا "نام تعداد"
                if "-" in s:
                    name_part, count_part = s.split("-", 1)
                else:
                    parts = s.rsplit(" ", 1)
                    if len(parts) == 2 and parts[1].strip().isdigit():
                        name_part, count_part = parts
                    else:
                        name_part, count_part = s, "1"

                name = name_part.strip()
                # فقط رقم‌ها را بردار (برای اعداد با فاصله یا کاراکترهای اضافی)
                digits = "".join(ch for ch in count_part if ch.isdigit())
                count = int(digits) if digits else 1
                if name:
                    result[name] = result.get(name, 0) + count

            elif isinstance(entry, dict):
                # اگر قبلاً تکی به صورت {"منجنیق": 2} بود
                for k, v in entry.items():
                    name = str(k).strip()
                    try:
                        count = int(v)
                    except:
                        count = 0
                    if name:
                        result[name] = result.get(name, 0) + count
        return result

    # هیچ چیز معتبر نبود
    return {}



async def view_province_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View specific province details for admin (safe & robust parsing)."""
    query = getattr(update, "callback_query", None)
    if query is None:
        logger.error("[view_province_admin] called without callback_query. Update: %s", update)
        if getattr(update, "effective_message", None):
            try:
                await update.effective_message.reply_text("❌ این عمل فقط از طریق دکمه‌ها قابل اجرا است.")
            except Exception:
                pass
        return

    await query.answer()
    callback_data = query.data or ""
    logger.debug(f"[view_province_admin] callback_data received: {callback_data}")

    try:
        m = re.match(r"^admin_view_province_(?P<country>[^_]+)_(?P<province>.+)$", callback_data)
        if not m:
            logger.error(f"[view_province_admin] unexpected callback_data format: {callback_data}")
            await query.edit_message_text("❌ خطا در تشخیص استان (فرمت داده نامعتبر).")
            return

        country = m.group("country")
        province = m.group("province").replace("_", " ").strip()

        province_info = load_province_data(country, province)
        province_info["structures"] = normalize_structures(province_info.get("structures", {}))
        if not province_info:
            text = f"❌ اطلاعات استان «{province}» در کشور «{country}» یافت نشد."
            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="admin_view_all_provinces")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return

        text = format_province_info(province_info)

        safe_prov = province.replace(" ", "_")
        # هر دکمه برگشت به منبع مشخص برمی‌گردد:
        keyboard = [
            [InlineKeyboardButton("🪙 معدن‌ها", callback_data=f"edit_province_mines_{country}_{safe_prov}")],
            [InlineKeyboardButton("💰 ثروت", callback_data=f"edit_province_wealth_{country}_{safe_prov}")],
            [InlineKeyboardButton("👥 جمعیت", callback_data=f"edit_province_population_{country}_{safe_prov}")],
            [InlineKeyboardButton("📈 مالیات", callback_data=f"edit_province_tax_{country}_{safe_prov}")],
            [InlineKeyboardButton("📊 محبوبیت", callback_data=f"edit_province_popularity_{country}_{safe_prov}")],
            [InlineKeyboardButton("🛡 سربازان", callback_data=f"edit_province_army_{country}_{safe_prov}")],
            [InlineKeyboardButton("🏰 قلعه", callback_data=f"edit_province_castle_{country}_{safe_prov}")],
            [InlineKeyboardButton("🏗 سازه‌ها", callback_data=f"edit_province_structures_{country}_{safe_prov}")],
            [InlineKeyboardButton("⚔️ سلاح‌ها", callback_data=f"edit_province_weapons_{country}_{safe_prov}")],
            [InlineKeyboardButton("📦 متفرقه", callback_data=f"edit_province_misc_{country}_{safe_prov}")],
            [InlineKeyboardButton("📦 اقلام اقتصادی", callback_data=f"edit_province_economic_items_{country}_{safe_prov}")],
            [InlineKeyboardButton("🏭 سازه‌های اقتصادی", callback_data=f"edit_province_economic_structures_{country}_{safe_prov}")],
            # این برگشت الان مشخص است: بازگشت به فهرست استان‌های همان کشور
            [InlineKeyboardButton("🔙 برگشت", callback_data=f"admin_country_provinces_{country}")]
        ]

        # علاوه بر callback_data برگشت، ما مقصد برگشت را برای حالت‌های پیام متنی (اگر نیاز بود) در user_data ذخیره می‌کنیم
        uid = query.from_user.id
        context.user_data.setdefault(uid, {})["last_viewed_province"] = {
            "country": country,
            "province": province,
            "back_to": f"admin_country_provinces_{country}"
        }

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    except Exception as e:
        logger.exception(f"Error in view_province_admin: {e}")
        try:
            await query.edit_message_text("❌ خطا در نمایش اطلاعات استان")
        except Exception:
            logger.error("Also failed to edit message after exception in view_province_admin")


async def handle_province_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle province field editing (determine field and set explicit back target)."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data or ""
    parts = callback_data.split("_")

    if len(parts) < 4 or parts[0] != "edit" or parts[1] != "province":
        await query.edit_message_text("❌ خطا در تشخیص داده‌ها")
        return

    # تعیین field_type و استخراج country/province
    if len(parts) >= 6 and parts[2] == "economic" and parts[3] in ["items", "structures"]:
        field_type = f"{parts[2]}_{parts[3]}"
        country = parts[4]
        province = "_".join(parts[5:]).replace("_", " ").strip()
    elif len(parts) >= 5:
        field_type = parts[2]
        country = parts[3]
        province = "_".join(parts[4:]).replace("_", " ").strip()
    else:
        await query.edit_message_text("❌ فرمت داده‌ها نامعتبر")
        return

    user_id = query.from_user.id
    context.user_data.setdefault(user_id, {})
    context.user_data[user_id].update({
        "editing_field": field_type,
        "editing_country": country,
        "editing_province": province,
        "province_name": province,
        "step": f"awaiting_province_{field_type}_edit",
        # ذخیره مقصد برگشت مشخص برای هنگامی که ویرایش کنسل یا پس از ذخیره می‌خواهیم برگردیم
        "edit_back_to": f"admin_view_province_{country}_{province.replace(' ', '_')}"
    })

    # بارگذاری داده‌ها (با fallback‌هایی که شما قبلاً گذاشته‌اید)
    province_data = load_province_data(country, province)
    province_data["structures"] = normalize_structures(province_data.get("structures", {}))
    if not province_data:
        # تلاش برای پیدا کردن با نام‌های جایگزین
        alternative_names = [province, province.strip(), province.replace(" ", "_"), province.replace("_", " ")]
        for alt in alternative_names:
            province_data = load_province_data(country, alt)
            if province_data:
                context.user_data[user_id]["editing_province"] = alt
                province = alt
                break

    if not province_data:
        # بررسی فایل‌های داخل پوشه provinces (همانند قبلی)
        try:
            possible_files = [
                f"provinces/{country}_{province.replace(' ', '_')}.json",
                f"provinces/{country}_{province}.json",
                f"provinces/{country}_{province.replace('_', ' ')}.json"
            ]
            for province_file in possible_files:
                if os.path.exists(province_file):
                    with open(province_file, "r", encoding="utf-8") as f:
                        province_data = json.load(f)
                    actual_province = os.path.basename(province_file).replace(f"{country}_", "").replace(".json", "")
                    context.user_data[user_id]["editing_province"] = actual_province
                    province = actual_province
                    break
        except Exception as e:
            logger.error(f"Error locating province file: {e}")

    if not province_data:
        await query.edit_message_text(
            f"❌ اطلاعات استان {province} در کشور {country} یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="admin_view_all_provinces")]])
        )
        return

    # حالا متن مناسب برای هر field_type را بسازیم (شبیه به کد شما، فقط کیبورد برگشت مشخص شده)
    text = ""
    if field_type == "mines":
        current_data = province_data.get("mines", {})
        mine_productions = province_data.get("mine_productions", {})
        text = f"⛏️ معدن‌های فعلی {province}:\n\n"
        for mine_name, count in current_data.items():
            weekly_income = mine_productions.get(mine_name, {}).get("weekly_per_unit", 0)
            total_weekly = count * weekly_income
            text += f"• {mine_name}: {count:,} معدن (درآمد هفتگی: {total_weekly:,})\n"
        text += "\n💡 فرمت جدید (پیشنهادی):\nنام - تعداد - درآمد هفتگی هر معدن\nمثال:\nCopper mine - 2 - 10000\n\n"
        text += "فرمت قدیمی: Copper mine:2,Gold mine:1"

    elif field_type == "wealth":
        current_wealth = province_data.get("wealth", 0)
        text = f"💰 ثروت فعلی {province}: {current_wealth:,}\n\nمقدار ثروت جدید را وارد کنید:"

    elif field_type == "population":
        current_pop = province_data.get("population", 0)
        text = f"👥 جمعیت فعلی {province}: {current_pop:,}\n\nمقدار جمعیت جدید را وارد کنید:"

    elif field_type == "tax":
        current_tax = province_data.get("tax", 0)
        text = f"📈 مالیات فعلی {province}: {current_tax}\n\nمقدار مالیات جدید را وارد کنید:"

    elif field_type == "popularity":
        current_pop = province_data.get("popularity", 0)
        text = f"📊 محبوبیت فعلی {province}: {current_pop}\n\nمقدار محبوبیت جدید را وارد کنید:"

    elif field_type == "army":
        current_army = province_data.get("army", {})
        text = f"🛡 سربازان فعلی {province}:\n\n"
        for unit, count in current_army.items():
            text += f"• {unit}: {count:,}\n"
        text += "\nسربازان جدید را با فرمت: نوع:تعداد,نوع2:تعداد"

    # elif field_type == "castle":
    #     current_castle = province_data.get("castle", [])
    #     text = f"🏰 قلعه فعلی {province}:\n\n"
    #     for i, item in enumerate(current_castle, 1):
    #         text += f"{i}. {item}\n"
    #     text += "\nآیتم‌های جدید هر خط یک مورد:"

    # elif field_type == "structures":
    #     current_structures = province_data.get("structures", [])
    #     text = f"🏗 سازه‌های فعلی {province}:\n\n"
    #     for i, item in enumerate(current_structures, 1):
    #         text += f"{i}. {item}\n"
    #     text += "\nسازه‌های جدید هر خط یک مورد:"
    
    # elif field_type == "weapons":
    #     current_weapons = province_data.get("weapons", [])
    #     text = f"⚔️ سلاح‌های فعلی {province}:\n\n"
    #     for i, item in enumerate(current_weapons, 1):
    #         text += f"{i}. {item}\n"
    #     text += "\nسلاح‌های جدید هر خط یک مورد:"

    # elif field_type == "misc":
    #     current_misc = province_data.get("misc", [])
    #     text = f"📦 متفرقه فعلی {province}:\n\n"
    #     for i, item in enumerate(current_misc, 1):
    #         text += f"{i}. {item}\n"
    #     text += "\nآیتم‌های جدید هر خط یک مورد:"

    elif field_type in ["structures", "weapons", "misc", "castle"]:
        current_data = province_data.get(field_type, {})
        text_map = {
            "structures": "🏗 سازه‌های",
            "weapons": "⚔️ سلاح‌های",
            "misc": "📦 متفرقه",
            "castle": "🏰 قلعه"
        }
        text = f"{text_map[field_type]} فعلی {province}:\n\n"
        for name, count in current_data.items():
            text += f"• {name}: {count}\n"
        text += "\nورودی جدید هر خط به فرمت زیر:\nنام - تعداد\nمثال:\nکشتی کوچک - 5\nمنجنیق ساده - 3"


    elif field_type == "economic_items":
        current_items = province_data.get("economic_items", {})
        text = f"📦 اقلام اقتصادی فعلی {province}:\n\n"
        all_item_names = set(current_items.keys()) | {
            "گندم", "گوشت", "ماهی", "مرغ", "میوه", "فولاد", "شیشه", "سنگ",
            "چوب", "جواهر", "پنبه", "پارچه", "چرم", "شراب",
            "Wheat", "Meat", "Fish", "Chicken", "Fruit", "Steel", "Glass", "Stone",
            "Wood", "Jewel", "Cotton", "Fabric", "Leather", "Wine"
        }
        for item_name in sorted(all_item_names):
            amount = current_items.get(item_name, 0)
            if amount > 0 or item_name in ["گندم", "گوشت", "ماهی", "مرغ", "میوه", "فولاد", "شیشه", "سنگ", "چوب", "جواهر", "پنبه", "پارچه", "چرم", "شراب"]:
                text += f"• {item_name}: {amount}\n"
        text += "\nفرمت جدید: نام کالا:مقدار,نام2:مقدار\nمثال: گندم:100,گوشت:50"

    elif field_type == "economic_structures":
        current_structures = province_data.get("economic_structures", {})
        text = f"🏭 سازه‌های اقتصادی فعلی {province}:\n\n"
        for struct_name, production_info in current_structures.items():
            count = production_info.get("count", 0)
            weekly_per_unit = production_info.get("weekly_output", 0)
            product = production_info.get("product", "نامشخص")
            total_weekly = count * weekly_per_unit
            text += f"• {struct_name}: {count:,} واحد (تولید: {total_weekly:,} {product} در هفته)\n"
        text += "\nفرمت جدید: نام سازه - تعداد - کالای تولیدی - تولید هفتگی هر واحد\nمثال:\nماهیگیری - 2 - ماهی - 10"

    else:
        text = "❌ نوع ویرایش نامشخص"

    # کیبورد با برگشت مشخص (edit_back_to ذخیره شده در user_data)
    back_cb = context.user_data[user_id].get("edit_back_to", f"admin_view_province_{country}_{province.replace(' ', '_')}")
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data=back_cb)]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_province_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = getattr(update, "message", None)
    user = update.effective_user
    user_id = user.id if user else None
    user_store = context.user_data.setdefault(user_id, {})

    field_type = user_store.get("editing_field")
    country = user_store.get("editing_country")
    province = user_store.get("editing_province")
    step = user_store.get("step")

    if not all([field_type, country, province, step]):
        return False
    if not str(step).startswith("awaiting_province_") or not str(step).endswith("_edit"):
        return False
    if not message or not getattr(message, "text", None):
        return False

    text_input = message.text.strip()

    try:
        province_data = load_province_data(country, province)
        if not province_data:
            await message.reply_text("❌ اطلاعات استان یافت نشد")
            return True

        success = False

        def to_int_safe(s):
            s = str(s).strip()
            s = re.sub(r"[,_\s]", "", s)
            return int(s)

        # (همان منطق پردازش که شما دارید — فقط در انتها BACK دقیقی ارسال می‌کنیم)
        if field_type == "economic_structures":
            economic_structures = {}
            lines = text_input.splitlines()
            for i, line in enumerate(lines, start=1):
                parts = [p.strip() for p in re.split(r"\s*-\s*", line)]
                if len(parts) >= 4:
                    try:
                        name = parts[0]
                        count = to_int_safe(parts[1])
                        product = parts[2]
                        weekly_per_unit = to_int_safe(parts[3])
                        economic_structures[name] = {"count": count, "product": product, "weekly_output": weekly_per_unit}
                    except Exception as e:
                        logger.warning(f"خطا در خط {i} سازه اقتصادی: {e}")
                        continue
                else:
                    logger.warning(f"فرمت نادرست در خط {i} سازه اقتصادی: {line}")
                    continue
            province_data["economic_structures"] = economic_structures
            success = True

        elif field_type == "mines":
            mines = {}
            mine_productions = province_data.get("mine_productions", {})
            lines = text_input.splitlines()
            for i, line in enumerate(lines, start=1):
                parts = [p.strip() for p in re.split(r"\s*-\s*", line)]
                if len(parts) >= 3:
                    try:
                        name = parts[0]
                        count = to_int_safe(parts[1])
                        weekly_income = to_int_safe(parts[2])
                        mines[name] = count
                        mine_productions[name] = {"weekly_per_unit": weekly_income}
                    except Exception as e:
                        logger.warning(f"خطا در خط {i} معدن: {e}")
                        continue
                else:
                    logger.warning(f"فرمت نادرست در خط {i} معدن: {line}")
                    continue
            province_data["mines"] = mines
            province_data["mine_productions"] = mine_productions
            success = True

        elif field_type == "army":
            army = {}
            pairs = [p.strip() for p in text_input.split(",") if p.strip()]
            for pair in pairs:
                if ":" in pair:
                    try:
                        unit, count = pair.split(":", 1)
                        army[unit.strip()] = to_int_safe(count)
                    except Exception as e:
                        logger.warning(f"خطا در پردازش ارتش: {e}")
                        continue
            province_data["army"] = army
            success = True

        # elif field_type == "castle":
        #     items = [line.strip() for line in text_input.splitlines() if line.strip()]
        #     province_data["castle"] = items
        #     success = True

        elif field_type == "economic_items":
            economic_items = {}
            pairs = [p.strip() for p in text_input.split(",") if p.strip()]
            for pair in pairs:
                if ":" in pair:
                    try:
                        item, amount = pair.split(":", 1)
                        economic_items[item.strip()] = to_int_safe(amount)
                    except Exception as e:
                        logger.warning(f"خطا در پردازش اقلام اقتصادی: {e}")
                        continue
            province_data["economic_items"] = economic_items
            success = True

        elif field_type in ["wealth", "population", "popularity"]:
            try:
                val = to_int_safe(text_input)
                province_data[field_type] = val
                success = True
            except Exception as e:
                logger.warning(f"خطا در پردازش {field_type}: {e}")
                success = False

        elif field_type == "tax":
            try:
                new_tax = int(text_input)
                if new_tax < 0 or new_tax > 100 or new_tax % 10 != 0:
                    await message.reply_text("❌ مقدار مالیات باید عددی بین ۰ تا ۱۰۰ و مضربی از ۱۰ باشد. لطفاً دوباره وارد کنید.")
                    return True
                province_data["tax"] = new_tax
                success = True
            except ValueError:
                await message.reply_text("❌ مقدار وارد شده معتبر نیست. لطفاً فقط عدد وارد کنید.")
                return True

        elif field_type == "structures":
            lines = [line.strip() for line in text_input.splitlines() if line.strip()]
            structures_dict = {}
            for line in lines:
                if "-" in line:
                    name, count = line.split("-", 1)
                    structures_dict[name.strip()] = int(count.strip())
                else:
                    structures_dict[line] = 1
            province_data["structures"] = structures_dict
            success = True
        
        elif field_type == "weapons":
            lines = [line.strip() for line in text_input.splitlines() if line.strip()]
            weapons_dict = {}
            for line in lines:
                if "-" in line:
                    name, count = line.split("-", 1)
                    weapons_dict[name.strip()] = int(count.strip())
                else:
                    weapons_dict[line] = 1
            province_data["weapons"] = weapons_dict
            success = True
        
        elif field_type == "misc":
            lines = [line.strip() for line in text_input.splitlines() if line.strip()]
            misc_dict = {}
            for line in lines:
                if "-" in line:
                    name, count = line.split("-", 1)
                    misc_dict[name.strip()] = int(count.strip())
                else:
                    misc_dict[line] = 1
            province_data["misc"] = misc_dict
            success = True
        
        elif field_type == "castle":
            lines = [line.strip() for line in text_input.splitlines() if line.strip()]
            castle_dict = {}
            for line in lines:
                if "-" in line:
                    name, count = line.split("-", 1)
                    castle_dict[name.strip()] = int(count.strip())
                else:
                    castle_dict[line] = 1
            province_data["castle"] = castle_dict
            success = True


        # elif field_type in ["structures", "weapons", "misc"]:
        #     items = [line.strip() for line in text_input.splitlines() if line.strip()]
        #     province_data[field_type] = items
        #     success = True

        else:
            logger.warning(f"نوع فیلد ناشناخته برای ویرایش: {field_type}")
            success = False

        if success:
            save_province_data(country, province, province_data)
            # برگشت به مقصد مشخص‌شده در user_store (edit_back_to)
            back_cb = user_store.get("edit_back_to", f"admin_view_province_{country}_{province.replace(' ', '_')}")
            await message.reply_text(
                f"✅ بخش «{field_type}» برای استان «{province}» به‌روزرسانی شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به استان", callback_data=back_cb)]
                ])
            )
            # پاک کردن استیت کاربر
            for k in ("step", "editing_field", "editing_country", "editing_province", "province_name", "edit_back_to"):
                user_store.pop(k, None)
        else:
            await message.reply_text("❌ خطا در پردازش داده‌ها. لطفاً فرمت صحیح را رعایت کنید.")

        return True

    except Exception as e:
        logger.exception(f"Exception in handle_province_edit_input: {e}")
        try:
            await message.reply_text("❌ خطا در ذخیره اطلاعات (داخل سرور). لطفاً بعداً تلاش کنید.")
        except Exception:
            logger.exception("Also failed to send error message to user.")
        return True


async def show_country_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show country admin menu for multi-country admins"""
    query = update.callback_query
    await query.answer()

    country = query.data.replace("admin_country_menu_", "")

    text = f"🌍 مدیریت کشور {country}"

    keyboard = [
        [InlineKeyboardButton("🏰 استان‌ها", callback_data=f"admin_country_provinces_{country}")],
        [InlineKeyboardButton("🔄 انتقالات", callback_data=f"admin_country_fers_{country}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_province_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_country_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show provinces for a specific country"""
    query = update.callback_query
    await query.answer()

    country = query.data.replace("admin_country_provinces_", "")
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Check access - allow both multi_country_admin and country_admin roles
    from callback_handlers import check_admin_access
    if not (check_admin_access(user_data, required_role="multi_country_admin") or 
            check_admin_access(user_data, required_country=country)):
        await query.edit_message_text("❌ دسترسی غیرمجاز.")
        return

    # Load countries data```tool_code
    try:
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        provinces = countries_data.get("countries_areas", {}).get(country, [])

        if not provinces:
            await query.edit_message_text(f"❌ هیچ استانی برای کشور {country} تعریف نشده است.")
            return

        text = f"🏰 استان‌های کشور {country.capitalize()}:\n\n"
        keyboard = []

        for i, province in enumerate(provinces, 1):
            text += f"{i}. {province}\n"
            keyboard.append([InlineKeyboardButton(f"📊 {province}", callback_data=f"admin_view_province_{country}_{province.replace(' ', '_')}")])

        keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data=f"admin_country_menu_{country}")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Error in show_country_provinces: {e}")
        await query.edit_message_text("❌ خطا در بارگذاری اطلاعات استان‌ها")

async def show_country_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transfers for a specific country"""
    query = update.callback_query
    await query.answer()

    country = query.data.replace("admin_country_transfers_", "")

    try:
        transfers_data = load_pending_transfers()
        country_transfers = [t for t in transfers_data.get("transfers", []) 
                           if t.get("source_country") == country or t.get("target_country") == country]

        if not country_transfers:
            text = f"📭 هیچ انتقالی برای کشور {country} وجود ندارد."
        else:
            text = f"🔄 انتقالات کشور {country}:\n\n"
            for i, transfer in enumerate(country_transfers, 1):
                text += f"{i}. {transfer.get('source_country', 'نامشخص')}-{transfer.get('source_province', 'نامشخص')} → "
                text += f"{transfer.get('target_country', 'نامشخص')}-{transfer.get('target_province', 'نامشخص')}\n"
                text += f"   📦 {transfer.get('item', 'نامشخص')} × {transfer.get('quantity', 0):,}\n"
                text += f"   📊 وضعیت: {transfer.get('status', 'نامشخص')}\n\n"

        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data=f"admin_country_menu_{country}")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logging.error(f"Error in show_country_transfers: {e}")
        await query.edit_message_text("❌ خطا در نمایش انتقالات")


# async def admin_manage_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Manage pending transfers"""
#     query = update.callback_query
#     await query.answer()

#     transfers_data = load_pending_transfers()
#     user_id = update.effective_user.id
#     # user_data = context.user_data.get(user_id, {})
#     user_data = context.user_data


#     pending_transfers = [t for t in transfers_data.get("transfers", []) if t.get("status") == "pending"]

#     text = "🔄 انتقالات در انتظار تایید:\n\n"
#     keyboard = []

#     for i, transfer in enumerate(pending_transfers):
#         text += (
#             f"{i+1}. {transfer.get('source_country', 'نامشخص')}-"
#             f"{transfer.get('source_province', 'نامشخص')} → "
#             f"{transfer.get('target_country', 'نامشخص')}-"
#             f"{transfer.get('target_province', 'نامشخص')}\n"
#         )

#         items = transfer.get('items', {}) or transfer.get('items_dict', {})
#         if items:
#             for item_name, quantity in items.items():
#                 text += f"   📦 {item_name} × {quantity:,}\n"
#         else:
#             text += "   📦 نامشخص × 0\n"

#         text += f"   🔄 نوع: {transfer.get('transfer_type', 'نامشخص')}\n\n"

#         keyboard.append([
#             InlineKeyboardButton(f"✅ تایید #{i+1}", callback_data=f"approve_transfer_{transfer.get('id', '')}"),
#             InlineKeyboardButton(f"❌ رد #{i+1}", callback_data=f"reject_transfer_{transfer.get('id', '')}")
#         ])

#     # تعیین مقصد برگشت دقیق بر اساس نقش / دسترسی
#     from callback_handlers import check_admin_access
#     if check_admin_access(user_data, required_role="master_admin"):
#         back_callback = "admin_province_menu"
#     elif check_admin_access(user_data, required_role="multi_country_admin"):
#         back_callback = "admin_province_menu"
#     else:
#         back_callback = "admin_menu"

#     keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data=back_callback)])
#     await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))



async def admin_manage_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage pending transfers (only for admins)"""
    query = update.callback_query
    print("DEBUG callback:", query.data)
    await query.answer()

    transfers_data = load_pending_transfers()
    pending_transfers = [t for t in transfers_data.get("transfers", []) if t.get("status") == "pending"]

    if not pending_transfers:
        text = "📭 هیچ انتقال در انتظار تأیید وجود ندارد."
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text = "🔄 انتقالات در انتظار تایید:\n\n"
    keyboard = []

    for i, transfer in enumerate(pending_transfers, 1):
        text += (
            f"{i}. {transfer.get('source_country', 'نامشخص')}-"
            f"{transfer.get('source_province', 'نامشخص')} → "
            f"{transfer.get('target_country', 'نامشخص')}-"
            f"{transfer.get('target_province', 'نامشخص')}\n"
        )

        items = transfer.get('items', {}) or transfer.get('items_dict', {})
        if items:
            for item_name, quantity in items.items():
                text += f"   📦 {item_name} × {quantity:,}\n"
        else:
            text += "   📦 نامشخص × 0\n"

        text += f"   🔄 نوع: {transfer.get('transfer_type', 'نامشخص')}\n\n"

        keyboard.append([
            InlineKeyboardButton(f"✅ تایید #{i}", callback_data=f"approve_transfer_{transfer.get('id', '')}"),
            InlineKeyboardButton(f"❌ رد #{i}", callback_data=f"reject_transfer_{transfer.get('id', '')}")
        ])

    # برگشت ساده فقط به منوی ادمین
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))



# async def approve_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Approve a pending transfer: add to target and subtract from source"""
#     query = update.callback_query
#     await query.answer()

#     transfer_id = query.data.replace("approve_transfer_", "")

#     try:
#         transfers_data = load_pending_transfers()
#         transfers = transfers_data.get("transfers", [])

#         target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)

#         if not target_transfer:
#             await query.edit_message_text("❌ انتقال پیدا نشد.")
#             return

#         target_transfer["status"] = "approved"
#         target_transfer["approved_at"] = datetime.utcnow().isoformat()

#         category = target_transfer.get("category")
#         items = target_transfer.get("items", {})

#         # مشخصات مبدا و مقصد
#         source_country = target_transfer.get("source_country")
#         source_province = target_transfer.get("source_province")
#         target_country = target_transfer.get("target_country")
#         target_province = target_transfer.get("target_province")

#         if not all([source_country, source_province, target_country, target_province, category, items]):
#             raise ValueError("Incomplete transfer data")

#         # لود داده مبدا و مقصد
#         source_data = load_province_data(source_country, source_province)
#         target_data = load_province_data(target_country, target_province)

#         if source_data is None:
#             raise FileNotFoundError(f"مبدا {source_country}_{source_province} پیدا نشد.")
#         if target_data is None:
#             # اگر مقصد نبود، یک فایل جدید بساز
#             target_data = {
#                 "country": target_country,
#                 "province": target_province,
#                 category: {}
#             }

#         # اطمینان از وجود بخش category
#         if category not in source_data:
#             source_data[category] = {}
#         if category not in target_data:
#             target_data[category] = {}

#         # انتقال آیتم‌ها
#         for item_name, amount in items.items():
#             if not isinstance(amount, int) or amount <= 0:
#                 continue

#             # کم‌کردن از مبدا
#             # current_source_amount = source_data[category].get(item_name, 0)
#             if isinstance(source_data[category], dict):
#                 current_source_amount = source_data[category].get(item_name, 0)
#             else:
#                 current_source_amount = source_data[category]

#             if current_source_amount < amount:
#                 raise ValueError(f"آیتم {item_name} در مبدا به اندازه کافی موجود نیست.")

#             # source_data[category][item_name] = current_source_amount - amount
#             if isinstance(source_data.get(category), dict):
#                 # اگر دیکشنری بود، به item_name مقدار بده
#                 source_data[category][item_name] = current_source_amount - amount
#             else:
#                 # اگر عدد بود، خود category یک مقدار عددی است (مثل ثروت)
#                 source_data[category] = current_source_amount - amount


#             # اضافه‌کردن به مقصد
#             # target_data[category][item_name] = target_data[category].get(item_name, 0) + amount
        
#             if isinstance(target_data.get(category), dict):
#                 target_data[category][item_name] = target_data[category].get(item_name, 0) + amount
#             else:
#                 # category خودش عدد هست، پس مستقیم جمع بزن
#                 target_data[category] = target_data.get(category, 0) + amount


#         # ذخیره‌سازی داده‌ها
#         save_province_data(source_country, source_province, source_data)
#         save_province_data(target_country, target_province, target_data)
#         # ارسال پیام به درخواست‌دهنده
#         requester_id = target_transfer.get("requester_id")
#         if requester_id:
#             try:
#                 await context.bot.send_message(
#                     chat_id=requester_id,
#                     text=(
#                         f"✅ انتقال شما تایید شد:\n"
#                         f"{source_country}-{source_province} → {target_country}-{target_province}\n"
#                         f"📦 {', '.join([f'{k} × {v:,}' for k, v in items.items()])}"
#                     )
#                 )
#             except Exception as e:
#                 logger.error(f"Error sending approval message: {e}")

#         transfers_data["transfers"] = [t for t in transfers if t.get("id") != transfer_id]
#         save_pending_transfers(transfers_data)

#         await query.edit_message_text("✅ انتقال تایید شد. آیتم‌ها منتقل شدند.")

#     except Exception as e:
#         import traceback
#         logger.error(f"Error approving transfer: {e}\n{traceback.format_exc()}")
#         await query.edit_message_text("❌ خطا در تایید انتقال")


# async def approve_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Approve a pending transfer: add to target and subtract from source"""
#     query = update.callback_query
#     await query.answer()

#     transfer_id = query.data.replace("approve_transfer_", "")

#     try:
#         transfers_data = load_pending_transfers()
#         transfers = transfers_data.get("transfers", [])

#         target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)
#         if not target_transfer:
#             await query.edit_message_text("❌ انتقال پیدا نشد.")
#             return

#         target_transfer["status"] = "approved"
#         target_transfer["approved_at"] = datetime.utcnow().isoformat()

#         category = target_transfer.get("category")
#         items = target_transfer.get("items", {})

#         source_country = target_transfer.get("source_country")
#         source_province = target_transfer.get("source_province")
#         target_country = target_transfer.get("target_country")
#         target_province = target_transfer.get("target_province")

#         if not all([source_country, source_province, target_country, target_province, category, items]):
#             raise ValueError("Incomplete transfer data")

#         # Load province data
#         source_data = load_province_data(source_country, source_province)
#         target_data = load_province_data(target_country, target_province)

#         if source_data is None:
#             raise FileNotFoundError(f"مبدا {source_country}_{source_province} پیدا نشد.")
#         if target_data is None:
#             target_data = {
#                 "country": target_country,
#                 "province": target_province,
#                 category: {} if isinstance(items, dict) else 0
#             }

#         # Ensure category exists
#         if category not in source_data:
#             source_data[category] = {} if isinstance(items, dict) else 0
#         if category not in target_data:
#             target_data[category] = {} if isinstance(items, dict) else 0

#         # Transfer items
#         if isinstance(items, dict):
#             # dict-type categories (structures, weapons, misc, castle, economic_items)
#             for item_name, amount in items.items():
#                 if not isinstance(amount, int) or amount <= 0:
#                     continue

#                 if not isinstance(source_data[category], dict):
#                     source_data[category] = {}
#                 if not isinstance(target_data[category], dict):
#                     target_data[category] = {}

#                 current_source_amount = source_data[category].get(item_name, 0)
#                 if current_source_amount < amount:
#                     raise ValueError(f"آیتم {item_name} در مبدا به اندازه کافی موجود نیست.")

#                 source_data[category][item_name] = current_source_amount - amount
#                 target_data[category][item_name] = target_data[category].get(item_name, 0) + amount
#         else:
#             # numeric-type categories (wealth, population, tax, popularity)
#             total_amount = sum(items.values()) if isinstance(items, dict) else items
#             source_data[category] = source_data.get(category, 0) - total_amount
#             target_data[category] = target_data.get(category, 0) + total_amount

#         # Save changes
#         save_province_data(source_country, source_province, source_data)
#         save_province_data(target_country, target_province, target_data)

#         # Notify requester
#         requester_id = target_transfer.get("requester_id")
#         if requester_id:
#             try:
#                 item_lines = []
#                 for k, v in items.items():
#                     item_lines.append(f"{k} × {v:,}")
#                 await context.bot.send_message(
#                     chat_id=requester_id,
#                     text=(
#                         f"✅ انتقال شما تایید شد:\n"
#                         f"{source_country}-{source_province} → {target_country}-{target_province}\n"
#                         f"📦 {', '.join(item_lines)}"
#                     )
#                 )
#             except Exception as e:
#                 logger.error(f"Error sending approval message: {e}")

#         # Remove transfer from pending
#         transfers_data["transfers"] = [t for t in transfers if t.get("id") != transfer_id]
#         save_pending_transfers(transfers_data)

#         await query.edit_message_text("✅ انتقال تایید شد. آیتم‌ها منتقل شدند.")

#     except Exception as e:
#         import traceback
#         logger.error(f"Error approving transfer: {e}\n{traceback.format_exc()}")
#         await query.edit_message_text("❌ خطا در تایید انتقال")


# async def approve_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Approve a pending transfer: add to target and subtract from source"""
#     query = update.callback_query
#     await query.answer()

#     transfer_id = query.data.replace("approve_transfer_", "")

#     try:
#         logger.info(f"Approving transfer ID: {transfer_id}")
#         transfers_data = load_pending_transfers()
#         transfers = transfers_data.get("transfers", [])

#         target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)
#         if not target_transfer:
#             await query.edit_message_text("❌ انتقال پیدا نشد.")
#             return

#         logger.info(f"Transfer data: {target_transfer}")

#         target_transfer["status"] = "approved"
#         target_transfer["approved_at"] = datetime.utcnow().isoformat()

#         category = target_transfer.get("category")
#         items = target_transfer.get("items", {})

#         logger.info(f"Category: {category}, Items: {items}, Items type: {type(items)}")

#         source_country = target_transfer.get("source_country")
#         source_province = target_transfer.get("source_province")
#         target_country = target_transfer.get("target_country")
#         target_province = target_transfer.get("target_province")

#         if not all([source_country, source_province, target_country, target_province, category, items]):
#             raise ValueError("Incomplete transfer data")

#         source_data = load_province_data(source_country, source_province)
#         target_data = load_province_data(target_country, target_province)

#         if source_data is None:
#             raise FileNotFoundError(f"مبدا {source_country}_{source_province} پیدا نشد.")
#         if target_data is None:
#             target_data = {
#                 "country": target_country,
#                 "province": target_province
#             }

#         logger.info(f"Source data before: {source_data}")
#         logger.info(f"Target data before: {target_data}")

#         # Convert wealth/population dict to int if needed
#         if category in ["wealth", "population"]:
#             if isinstance(items, dict):
#                 items = sum(items.values())  # تبدیل dict به عدد
#             elif not isinstance(items, int):
#                 raise ValueError("فرمت مقدار نامعتبر است.")

#         # Ensure category exists
#         if category not in source_data:
#             source_data[category] = {} if isinstance(items, dict) else 0
#         if category not in target_data:
#             target_data[category] = {} if isinstance(items, dict) else 0

#         # Transfer process
#         if isinstance(items, dict):
#             logger.info("Processing dict transfer...")
#             for item_name, amount in items.items():
#                 logger.info(f"Item: {item_name}, Amount: {amount}")
#                 if not isinstance(amount, int) or amount <= 0:
#                     continue

#                 if not isinstance(source_data[category], dict):
#                     source_data[category] = {}
#                 if not isinstance(target_data[category], dict):
#                     target_data[category] = {}

#                 current_source_amount = source_data[category].get(item_name, 0)
#                 if current_source_amount < amount:
#                     raise ValueError(f"آیتم {item_name} در مبدا به اندازه کافی موجود نیست.")

#                 source_data[category][item_name] = current_source_amount - amount
#                 target_data[category][item_name] = target_data[category].get(item_name, 0) + amount
#         else:
#             logger.info("Processing numeric transfer...")
#             if category not in ["wealth", "population"]:
#                 raise ValueError(f"انتقال برای دسته {category} مجاز نیست.")

#             if not isinstance(items, int) or items <= 0:
#                 raise ValueError("مقدار انتقال نامعتبر است.")

#             current_source_amount = source_data.get(category, 0)
#             if current_source_amount < items:
#                 raise ValueError(f"{category} در مبدا به اندازه کافی موجود نیست.")

#             source_data[category] = current_source_amount - items
#             target_data[category] = target_data.get(category, 0) + items

#         logger.info(f"Source data after: {source_data}")
#         logger.info(f"Target data after: {target_data}")

#         # Save updated province data
#         save_province_data(source_country, source_province, source_data)
#         save_province_data(target_country, target_province, target_data)

#         # Notify requester
#         requester_id = target_transfer.get("requester_id")
#         if requester_id:
#             try:
#                 if isinstance(items, dict):
#                     item_lines = [f"{k} × {v:,}" for k, v in items.items()]
#                 else:
#                     item_lines = [f"{category} × {items:,}"]

#                 await context.bot.send_message(
#                     chat_id=requester_id,
#                     text=(
#                         f"✅ انتقال شما تایید شد:\n"
#                         f"{source_country}-{source_province} → {target_country}-{target_province}\n"
#                         f"📦 {', '.join(item_lines)}"
#                     )
#                 )
#             except Exception as e:
#                 logger.error(f"Error sending approval message: {e}")

#         # Remove approved transfer from pending list
#         transfers_data["transfers"] = [t for t in transfers if t.get("id") != transfer_id]
#         save_pending_transfers(transfers_data)

#         await query.edit_message_text("✅ انتقال تایید شد. آیتم‌ها منتقل شدند.")

#     except Exception as e:
#         import traceback
#         logger.error(f"Error approving transfer: {e}\n{traceback.format_exc()}")
#         await query.edit_message_text(f"❌ خطا در تایید انتقال: {e}")



# async def reject_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Reject a pending transfer"""
#     query = update.callback_query
#     await query.answer()

#     transfer_id = query.data.replace("reject_transfer_", "")

#     try:
#         transfers_data = load_pending_transfers()
#         transfers = transfers_data.get("transfers", [])

#         target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)
#         if not target_transfer:
#             await query.edit_message_text("❌ انتقال پیدا نشد.")
#             return

#         # تغییر وضعیت
#         target_transfer["status"] = "rejected"
#         target_transfer["rejected_at"] = datetime.utcnow().isoformat()

#         # پیام به درخواست‌دهنده
#         requester_id = target_transfer.get("requester_id")
#         if requester_id:
#             try:
#                 items = target_transfer.get("items", {})
#                 source_country = target_transfer.get("source_country")
#                 source_province = target_transfer.get("source_province")
#                 target_country = target_transfer.get("target_country")
#                 target_province = target_transfer.get("target_province")

#                 await context.bot.send_message(
#                     chat_id=requester_id,
#                     text=(
#                         f"❌ انتقال شما رد شد:\n"
#                         f"{source_country}-{source_province} → {target_country}-{target_province}\n"
#                         f"📦 {', '.join([f'{k} × {v:,}' for k, v in items.items()])}"
#                     )
#                 )
#             except Exception as e:
#                 logger.error(f"Error sending rejection message: {e}")

#         # حذف از لیست انتقالات
#         transfers_data["transfers"] = [t for t in transfers if t.get("id") != transfer_id]
#         save_pending_transfers(transfers_data)

#         await query.edit_message_text("❌ انتقال رد شد و از لیست حذف گردید.")

#     except Exception as e:
#         logger.error(f"Error rejecting transfer: {e}")
#         await query.edit_message_text("❌ خطا در رد انتقال")


async def approve_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a pending transfer: add to target and subtract from source"""
    query = update.callback_query
    await query.answer()

    transfer_id = query.data.replace("approve_transfer_", "")

    try:
        logger.info(f"Approving transfer ID: {transfer_id}")
        transfers_data = load_pending_transfers()
        transfers = transfers_data.get("transfers", [])

        target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)
        if not target_transfer:
            await query.edit_message_text("❌ انتقال پیدا نشد.")
            return

        # تغییر وضعیت
        target_transfer["status"] = "approved"
        target_transfer["approved_at"] = datetime.utcnow().isoformat()

        category = target_transfer.get("category")
        items = target_transfer.get("items", {})

        source_country = target_transfer.get("source_country")
        source_province = target_transfer.get("source_province")
        target_country = target_transfer.get("target_country")
        target_province = target_transfer.get("target_province")

        if not all([source_country, source_province, target_country, target_province, category, items]):
            raise ValueError("Incomplete transfer data")

        # لود داده‌های مبدا و مقصد
        source_data = load_province_data(source_country, source_province)
        target_data = load_province_data(target_country, target_province) or {
            "country": target_country,
            "province": target_province
        }

        # تبدیل و آماده‌سازی مقادیر
        if category in ["wealth", "population"]:
            if isinstance(items, dict):
                items = sum(items.values())
            elif not isinstance(items, int):
                raise ValueError("فرمت مقدار نامعتبر است.")

        if category not in source_data:
            source_data[category] = {} if isinstance(items, dict) else 0
        if category not in target_data:
            target_data[category] = {} if isinstance(items, dict) else 0

        # فرآیند انتقال
        if isinstance(items, dict):
            for item_name, amount in items.items():
                if not isinstance(amount, int) or amount <= 0:
                    continue

                if not isinstance(source_data[category], dict):
                    source_data[category] = {}
                if not isinstance(target_data[category], dict):
                    target_data[category] = {}

                current_source_amount = source_data[category].get(item_name, 0)
                if current_source_amount < amount:
                    raise ValueError(f"آیتم {item_name} در مبدا به اندازه کافی موجود نیست.")

                source_data[category][item_name] = current_source_amount - amount
                target_data[category][item_name] = target_data[category].get(item_name, 0) + amount
        else:
            if category not in ["wealth", "population"]:
                raise ValueError(f"انتقال برای دسته {category} مجاز نیست.")

            if not isinstance(items, int) or items <= 0:
                raise ValueError("مقدار انتقال نامعتبر است.")

            current_source_amount = source_data.get(category, 0)
            if current_source_amount < items:
                raise ValueError(f"{category} در مبدا به اندازه کافی موجود نیست.")

            source_data[category] = current_source_amount - items
            target_data[category] = target_data.get(category, 0) + items

        # ذخیره داده‌های مبدا و مقصد
        save_province_data(source_country, source_province, source_data)
        save_province_data(target_country, target_province, target_data)

        # اطلاع‌رسانی به درخواست‌دهنده
        requester_id = target_transfer.get("requester_id")
        if requester_id:
            try:
                if isinstance(items, dict):
                    item_lines = [f"{k} × {v:,}" for k, v in items.items()]
                else:
                    item_lines = [f"{category} × {items:,}"]

                await context.bot.send_message(
                    chat_id=requester_id,
                    text=(
                        f"✅ انتقال شما تایید شد:\n"
                        f"{source_country}-{source_province} → {target_country}-{target_province}\n"
                        f"📦 {', '.join(item_lines)}"
                    )
                )
            except Exception as e:
                logger.error(f"Error sending approval message: {e}")

        # ذخیره تغییر وضعیت (بدون حذف)
        save_pending_transfers(transfers_data)

        await query.edit_message_text("✅ انتقال تایید شد. آیتم‌ها منتقل شدند.")

    except Exception as e:
        import traceback
        logger.error(f"Error approving transfer: {e}\n{traceback.format_exc()}")
        await query.edit_message_text(f"❌ خطا در تایید انتقال: {e}")


async def reject_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject a pending transfer"""
    query = update.callback_query
    await query.answer()

    transfer_id = query.data.replace("reject_transfer_", "")

    try:
        transfers_data = load_pending_transfers()
        transfers = transfers_data.get("transfers", [])

        target_transfer = next((t for t in transfers if t.get("id") == transfer_id), None)
        if not target_transfer:
            await query.edit_message_text("❌ انتقال پیدا نشد.")
            return

        # تغییر وضعیت
        target_transfer["status"] = "rejected"
        target_transfer["rejected_at"] = datetime.utcnow().isoformat()

        # پیام به درخواست‌دهنده
        requester_id = target_transfer.get("requester_id")
        if requester_id:
            try:
                items = target_transfer.get("items", {})
                source_country = target_transfer.get("source_country")
                source_province = target_transfer.get("source_province")
                target_country = target_transfer.get("target_country")
                target_province = target_transfer.get("target_province")

                if isinstance(items, dict):
                    item_lines = [f"{k} × {v:,}" for k, v in items.items()]
                else:
                    item_lines = [f"{items}"]

                await context.bot.send_message(
                    chat_id=requester_id,
                    text=(
                        f"❌ انتقال شما رد شد:\n"
                        f"{source_country}-{source_province} → {target_country}-{target_province}\n"
                        f"📦 {', '.join(item_lines)}"
                    )
                )
            except Exception as e:
                logger.error(f"Error sending rejection message: {e}")

        # ذخیره تغییر وضعیت (بدون حذف)
        save_pending_transfers(transfers_data)

        await query.edit_message_text("❌ انتقال رد شد.")

    except Exception as e:
        logger.error(f"Error rejecting transfer: {e}")
        await query.edit_message_text("❌ خطا در رد انتقال")


async def admin_manage_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage shop items"""
    query = update.callback_query
    await query.answer()

    text = "🛍 مدیریت فروشگاه"

    keyboard = [
        [InlineKeyboardButton("➕ افزودن آیتم", callback_data="admin_add_shop_item")],
        [InlineKeyboardButton("📋 مشاهده آیتم‌ها", callback_data="admin_view_shop_items")],
        [InlineKeyboardButton("🛑 قفل فروشگاه", callback_data="admin_lock_shop")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_province_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_shop_item_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt for adding shop item"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    context.user_data[user_id] = context.user_data.get(user_id, {})
    context.user_data[user_id]["step"] = "awaiting_shop_item_image"

    await query.edit_message_text(
        "📸 لطفاً تصویر آیتم جدید را ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="admin_manage_shop")]])
    )

async def handle_shop_item_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop item image upload"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})

    if user_data.get("step") != "awaiting_shop_item_image":
        return

    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return

    # Store photo
    photo = update.message.photo[-1].file_id
    context.user_data[user_id]["shop_item_data"] = {"photo": photo}

    # Request item name
    await update.message.reply_text(
        "✅ تصویر دریافت شد.\n\n📝 نام آیتم را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
        ]])
    )

    context.user_data[user_id]["step"] = "awaiting_shop_item_name"


async def handle_shop_item_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop item text inputs with improved checks and logging"""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    # اطمینان از وجود دیکشنری shop_item_data
    if user_id not in context.user_data:
        context.user_data[user_id] = {}
    if "shop_item_data" not in context.user_data[user_id]:
        context.user_data[user_id]["shop_item_data"] = {}

    user_data = context.user_data[user_id]
    step = user_data.get("step")

    print(f"[handle_shop_item_text_input] user_id={user_id} step={step} text='{text}'")

    if step == "awaiting_shop_item_name":
        user_data["shop_item_data"]["name"] = text
        await update.message.reply_text(
            "📝 نوع آیتم را وارد کنید:\n(مثال: Army, Castle, Structure, Weapon, Misc, EconStructure)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_type"

    elif step == "awaiting_shop_item_type":
        user_data["shop_item_data"]["type"] = text
        await update.message.reply_text(
            "🌍 کشور مربوطه را وارد کنید:\n(مثال: Alpyr, Aldemar, Walden, All)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_country"

    elif step == "awaiting_shop_item_country":
        countries = [c.strip() for c in text.split(",") if c.strip()]
        user_data["shop_item_data"]["countries"] = countries
        await update.message.reply_text(
            "🏷 هشتگ‌ها را وارد کنید (با # و با کاما جدا کنید):\nمثال: #All, #Alpyr, #Santos",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_hashtags"

    elif step == "awaiting_shop_item_hashtags":
        hashtags = [tag.strip() for tag in text.split(",") if tag.strip()]
        user_data["shop_item_data"]["hashtags"] = hashtags
        await update.message.reply_text(
            "📄 توضیحات آیتم را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_description"

    # elif step == "awaiting_shop_item_description":
    #     user_data["shop_item_data"]["description"] = text
    #     item_type = user_data["shop_item_data"].get("type", "").lower()
    #     print(f"[handle_shop_item_text_input] item_type={item_type}")
    #     if item_type == "army":
    #         await update.message.reply_text(
    #             "🔢 تعداد سرباز را وارد کنید:",
    #             reply_markup=InlineKeyboardMarkup([[
    #                 InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
    #             ]])
    #         )
    #         user_data["step"] = "awaiting_shop_item_count"
    #     else:
    #         await update.message.reply_text(
    #             "💰 قیمت و مواد مورد نیاز را وارد کنید:",
    #             reply_markup=InlineKeyboardMarkup([[
    #                 InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
    #             ]])
    #         )
    #         user_data["step"] = "awaiting_shop_item_price"

    elif step == "awaiting_shop_item_description":
        user_data["shop_item_data"]["description"] = text
        item_type = user_data["shop_item_data"].get("type", "").lower()
        print(f"[handle_shop_item_text_input] item_type={item_type}")
    
        # دسته‌هایی که نیاز به گرفتن تعداد دارند
        count_required_types = ["army", "weapons", "misc", "castle", "structures"]
    
        if item_type in count_required_types:
            await update.message.reply_text(
                "🔢 تعداد آیتم را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
                ]])
            )
            user_data["step"] = "awaiting_shop_item_count"
        else:
            await update.message.reply_text(
                "💰 قیمت و مواد مورد نیاز را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
                ]])
            )
            user_data["step"] = "awaiting_shop_item_price"


    elif step == "awaiting_shop_item_count":
        if not text.isdigit():
            await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید.")
            return
        user_data["shop_item_data"]["count"] = int(text)
        print(f"[handle_shop_item_text_input] count={text}")
        await update.message.reply_text(
            "💰 قیمت و مواد مورد نیاز را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_price"

    elif step == "awaiting_shop_item_price":
        user_data["shop_item_data"]["price"] = text
        await update.message.reply_text(
            "👤 آیدی مالک را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_manage_shop")
            ]])
        )
        user_data["step"] = "awaiting_shop_item_owner"

    elif step == "awaiting_shop_item_owner":
        user_data["shop_item_data"]["owner_id"] = text
        # چک قبل از ارسال
        if "type" not in user_data["shop_item_data"]:
            await update.message.reply_text("❌ خطا: نوع آیتم مشخص نیست.")
            print("[handle_shop_item_text_input] ERROR: 'type' not found in shop_item_data")
            return
        await generate_shop_item_post(update, context)

    else:
        await update.message.reply_text("❌ مرحله نامشخص یا نامعتبر است.")
        print(f"[handle_shop_item_text_input] ERROR: unknown step '{step}'")


async def admin_edit_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing a shop item"""
    logger.info("✅ admin_edit_shop_item triggered")
    query = update.callback_query
    await query.answer()
    
    logger.info("✅ هندلر admin_edit_shop_item فراخوانی شد.")
    logger.info(f"callback_data دریافت‌شده: {query.data}")

    user_id = query.from_user.id
    item_id = query.data.replace("admin_edit_shop_item_", "")
    logger.info(f"شناسه آیتم: {item_id}")

    context.user_data[user_id] = context.user_data.get(user_id, {})
    context.user_data[user_id]["editing_shop_item_id"] = item_id
    context.user_data[user_id]["step"] = "awaiting_edit_choice"

    text = f"✏️ ویرایش آیتم فروشگاه\n🆔 آیتم ID: {item_id}\n\nچه بخشی را می‌خواهید ویرایش کنید؟"

    keyboard = [
        [InlineKeyboardButton("📸 تصویر", callback_data="edit_shop_image"),
         InlineKeyboardButton("📝 توضیحات", callback_data="edit_shop_caption")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="admin_view_shop_items")]
    ]

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_delete_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a shop item with confirmation"""
    logger.info("✅ admin_delete_shop_item triggered")
    query = update.callback_query
    await query.answer()

    item_id = query.data.replace("admin_delete_shop_item_", "")

    text = f"🗑️ حذف آیتم فروشگاه\n🆔 آیتم ID: {item_id}\n\n⚠️ آیا مطمئن هستید که می‌خواهید این آیتم را حذف کنید؟\n\nاین عمل غیرقابل برگشت است!"

    keyboard = [
        [InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"confirm_delete_shop_item_{item_id}"),
         InlineKeyboardButton("❌ انصراف", callback_data="admin_view_shop_items")]
    ]

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_delete_shop_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and delete shop item"""
    logger.info("✅ confirm_delete_shop_item triggered")
    query = update.callback_query
    await query.answer()

    item_id = query.data.replace("confirm_delete_shop_item_", "")

    try:
        logger.info(f"Trying to delete shop item, received callback item_id: {item_id}")
        from shop_handler import delete_shop_item
        if delete_shop_item(item_id):
            text = f"✅ آیتم با شناسه {item_id} با موفقیت حذف شد."
            back_button_cb = "admin_manage_shop"
        else:
            text = f"❌ خطا در حذف آیتم {item_id}. ممکن است آیتم وجود نداشته باشد."
            back_button_cb = "admin_view_shop_items"
    except Exception as e:
        logger.error(f"Error deleting shop item: {e}")
        text = "❌ خطا در حذف آیتم."
        back_button_cb = "admin_view_shop_items"

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 برگشت", callback_data=back_button_cb)
    ]])

    if query.message and query.message.text:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=reply_markup
        )


async def admin_show_economy_overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show economic overview for admin selected province"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    province = user_data.get("selected_province")
    country = user_data.get("selected_country_for_province")

    if not province or not country:
        await query.edit_message_text("❌ خطا در تشخیص استان یا کشور. لطفاً ابتدا وارد منوی مدیریت کشور شوید.")
        return

    # Load province data
    province_info = load_province_data(country, province)
    if not province_info:
        await query.edit_message_text(f"❌ اطلاعات استان {province} در کشور {country} یافت نشد.")
        return

    # بارگذاری لیست استان‌های کشور برای تشخیص پایتخت
    with open("countries.json", "r", encoding="utf-8") as f:
        countries_data = json.load(f)
    provinces = countries_data.get("countries_areas", {}).get(country, [])
    is_capital = (province == provinces[0])

    # اطلاعات اولیه
    population = province_info.get("population", 0)
    wealth = province_info.get("wealth", 0)

    # محاسبه درآمد معدن و مالیات
    mine_income, mine_details = calculate_weekly_income(province_info)
    tax_income = calculate_tax_income(province_info)
    total_weekly_income = mine_income + tax_income

    # محاسبه تولیدات اقتصادی
    if population > 0:
        production_results, prod_details = calculate_weekly_production(province_info)
    else:
        production_results, prod_details = {}, []

    # محاسبه تغییر محبوبیت
    popularity_change = calculate_hunger_and_consumption_popularity(province) + calculate_tax_popularity(province)
    tax_popularity_change = calculate_tax_popularity(province)
    hunger_consumption_change = calculate_hunger_and_consumption_popularity(province)


    # ساخت متن نهایی
    text = f"📊 نمای کلی اقتصاد - {province}\n"
    text += f"🌍 کشور: {country}\n\n"

    text += "💰 درآمد هفتگی:\n"
    if total_weekly_income > 0:
        text += f"  • کل درآمد: {total_weekly_income:,} طلا\n"
        if mine_income > 0:
            text += f"    - معادن: {mine_income:,} طلا\n"
        if tax_income > 0:
            text += f"    - مالیات: {tax_income:,} طلا\n"
    else:
        text += "  • 0\n"

    # text += "\n📊 تغییرات محبوبیت:\n"
    # if popularity_change != 0:
    #     change_str = f"+{popularity_change}" if popularity_change > 0 else str(popularity_change)
    #     text += f"  • {change_str} (مالیات، تغذیه، اولویت غلات)\n"
    # else:
    #     text += "  • 0\n"
    
    text += "\n📊 تغییرات محبوبیت:\n"

    # بخش مالیات
    if tax_popularity_change != 0:
        change_str = f"+{tax_popularity_change}" if tax_popularity_change > 0 else str(tax_popularity_change)
        text += f"  • {change_str} (مالیات)\n"
    else:
        text += "  • 0 (مالیات)\n"
    
    # بخش مصرف غلات
    if hunger_consumption_change != 0:
        change_str = f"+{hunger_consumption_change}" if hunger_consumption_change > 0 else str(hunger_consumption_change)
        text += f"  • {change_str} (مصرف غلات/ضریب مصرف)\n"
    else:
        text += "  • 0 (مصرف غلات/ضریب مصرف)\n"


    text += "\n🏭 تولید هفتگی:\n"
    if production_results and population > 0:
        for item, amount in production_results.items():
            text += f"  • {item}: +{amount:,}\n"
    else:
        text += "  • 0\n"

    text += f"\n\n👥 جمعیت: {population:,} نفر"
    text += f"\n💰 ثروت فعلی: {wealth:,} طلا"

    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))



async def handle_shop_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop item edit choice"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    context.user_data[user_id] = context.user_data.get(user_id, {})

    if query.data == "edit_shop_image":
        context.user_data[user_id]["step"] = "awaiting_new_shop_image"
        await query.edit_message_text(
            "📸 تصویر جدید را ارسال کنید:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_view_shop_items")
            ]])
        )
        return

    elif query.data == "edit_shop_caption":
        # ست‌کردن مرحلهٔ انتظار متن برای ویرایش
        context.user_data[user_id]["step"] = "awaiting_new_shop_caption"


        example = (
        "📝 لطفاً اطلاعات جدید آیتم را طبق یکی از قالب‌های زیر وارد کنید:\n\n"
        "📌 **مثال چند‌خطی (کلید: مقدار)**\n"
        "نام: شمشیر جادویی\n"
        "نوع: Weapon\n"
        "کشور: Santos, Alpyr\n"
        "قیمت: 32000\n"
        "مواد: آهن:50, چوب:20\n"
        "تعداد: 5\n"
        "توضیحات: این شمشیر قدرت حمله را دو برابر می‌کند.\n"
        "هشتگ‌ها: #Santos #Weapon\n"
        "ایدی سازنده: @creator_id\n\n"
        "🧠 فقط فیلدهایی که میخوای تغییر کنن رو وارد کن."
    )


        # ارسال بدون parse_mode تا از خطاهای entity جلوگیری شود
        await query.edit_message_text(
            example,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 انصراف", callback_data="admin_view_shop_items")
            ]])
        )
        return

    # در صورت مواجهه با callback غیرمنتظره، برگرد به منوی مدیریت
    await query.edit_message_text(
        "⚠️ انتخاب نامعتبر. در حال بازگشت به منوی مدیریت فروشگاه.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")]])
    )


import re

# def parse_shop_item_text(text: str) -> dict:
#     import re

#     if not text:
#         return {}

#     text = text.strip()
#     if '\n' not in text and ':' not in text:
#         return {"description": text}

#     updates = {}
#     lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

#     for line in lines:
#         if ':' not in line:
#             updates.setdefault("description", "")
#             if updates["description"]:
#                 updates["description"] += "\n"
#             updates["description"] += line
#             continue

#         key, val = map(str.strip, line.split(':', 1))
#         kl = key.lower()

#         if kl in ("نام", "name"):
#             updates["name"] = val

#         elif kl in ("نوع", "type"):
#             updates["type"] = val

#         elif kl in ("کشور", "country", "کشورها", "countries"):
#             # اگر val رشته است، تفکیک به لیست
#             countries = []
#             if isinstance(val, str):
#                 countries = re.split(r'[,\s]+', val)
#                 countries = [c.strip() for c in countries if c.strip()]
#             elif isinstance(val, list):
#                 countries = val
#             updates["country"] = countries  # بهتره کلید اصلی country باشه، چون دیتابیس همین رو داره

#         elif kl in ("قیمت", "price"):
#             num = re.sub(r"[^\d]", "", val)
#             if num:
#                 try:
#                     updates["price"] = int(num)
#                 except:
#                     pass

#         elif kl in ("تعداد", "count", "موجودی"):
#             num = re.sub(r"[^\d]", "", val)
#             if num:
#                 try:
#                     updates["count"] = int(num)
#                 except:
#                     pass

#         elif kl in ("توضیحات", "description", "شرح"):
#             updates["description"] = val

#         elif kl in ("مواد", "materials"):
#             mats = {}
#             parts = re.split(r'[,\;]', val)
#             for part in parts:
#                 part = part.strip()
#                 if not part:
#                     continue
#                 if '=' in part:
#                     mkey, mval = map(str.strip, part.split('=', 1))
#                 elif ':' in part:
#                     mkey, mval = map(str.strip, part.split(':', 1))
#                 else:
#                     m = re.match(r'(.+?)\s+(\d+)', part)
#                     if m:
#                         mkey, mval = m.group(1).strip(), m.group(2).strip()
#                     else:
#                         continue
#                 num = re.sub(r"[^\d]", "", mval)
#                 try:
#                     mats[mkey] = int(num) if num else 0
#                 except:
#                     mats[mkey] = 0
#             updates["materials"] = mats

#         elif kl in ("هشتگ", "هشتگ‌ها", "hashtags", "برچسب", "برچسب‌ها"):
#             tags = []
#             if isinstance(val, str):
#                 tags = re.findall(r'#\w+', val)
#                 if not tags:
#                     parts = re.split(r'[,\s]+', val)
#                     tags = [('#' + p.strip()) if p and not p.strip().startswith('#') else p.strip() for p in parts if p.strip()]
#             elif isinstance(val, list):
#                 tags = val
#             updates["hashtags"] = tags

#         elif kl in ("ایدی سازنده", "سازنده", "owner", "فروشنده", "مالک"):
#             updates["owner"] = val

#         else:
#             updates.setdefault("description", "")
#             if updates["description"]:
#                 updates["description"] += "\n"
#             updates["description"] += f"{key}: {val}"

#     # اگر داده‌های قبلی رشته بودن ولی الان باید لیست باشن، مثلا country
#     if "country" in updates and isinstance(updates["country"], str):
#         updates["country"] = [c.strip() for c in re.split(r'[,\s]+', updates["country"]) if c.strip()]

#     # همین‌طور برای hashtags اگر رشته بود
#     if "hashtags" in updates and isinstance(updates["hashtags"], str):
#         updates["hashtags"] = [t.strip() for t in updates["hashtags"].split() if t.strip()]

#     return updates


def parse_shop_item_text(text: str, item_type: str = "") -> dict:
    """
    Parse multiline shop item text into a dictionary.
    پشتیبانی از: name, type, country, price, count, description, materials, hashtags, owner
    item_type: برای تعیین آیتم‌هایی که نیاز به count پیش‌فرض دارند (misc, weapons, castle, structures)
    """
    import re

    if not text:
        return {}

    text = text.strip()
    if '\n' not in text and ':' not in text:
        return {"description": text}

    updates = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for line in lines:
        if ':' not in line:
            updates.setdefault("description", "")
            if updates["description"]:
                updates["description"] += "\n"
            updates["description"] += line
            continue

        key, val = map(str.strip, line.split(':', 1))
        kl = key.lower()

        if kl in ("نام", "name"):
            updates["name"] = val

        elif kl in ("نوع", "type"):
            updates["type"] = val
            item_type = val.lower()  # ذخیره نوع آیتم برای استفاده بعدی

        elif kl in ("کشور", "country", "کشورها", "countries"):
            countries = []
            if isinstance(val, str):
                countries = re.split(r'[,\s]+', val)
                countries = [c.strip() for c in countries if c.strip()]
            elif isinstance(val, list):
                countries = val
            updates["country"] = countries
            updates["countries"] = countries

        elif kl in ("قیمت", "price"):
            num = re.sub(r"[^\d]", "", val)
            if num:
                try:
                    updates["price"] = int(num)
                except:
                    pass

        elif kl in ("تعداد", "count", "موجودی"):
            num = re.sub(r"[^\d]", "", val)
            if num:
                try:
                    updates["count"] = int(num)
                except:
                    updates["count"] = 0
            else:
                # برای آیتم‌های قابل شمارش، اگر تعداد داده نشده بود، پیش‌فرض 1
                if item_type in ("misc", "weapons", "castle", "structures", "army"):
                    updates["count"] = 1

        elif kl in ("توضیحات", "description", "شرح"):
            updates["description"] = val

        elif kl in ("مواد", "materials"):
            mats = {}
            parts = re.split(r'[,\;]', val)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if '=' in part:
                    mkey, mval = map(str.strip, part.split('=', 1))
                elif ':' in part:
                    mkey, mval = map(str.strip, part.split(':', 1))
                else:
                    m = re.match(r'(.+?)\s+(\d+)', part)
                    if m:
                        mkey, mval = m.group(1).strip(), m.group(2).strip()
                    else:
                        continue
                num = re.sub(r"[^\d]", "", mval)
                try:
                    mats[mkey] = int(num) if num else 0
                except:
                    mats[mkey] = 0
            updates["materials"] = mats

        elif kl in ("هشتگ", "هشتگ‌ها", "hashtags", "برچسب", "برچسب‌ها"):
            tags = []
            if isinstance(val, str):
                tags = re.findall(r'#\w+', val)
                if not tags:
                    parts = re.split(r'[,\s]+', val)
                    tags = [('#' + p.strip()) if p and not p.strip().startswith('#') else p.strip() for p in parts if p.strip()]
            elif isinstance(val, list):
                tags = val
            updates["hashtags"] = tags

        elif kl in ("ایدی سازنده", "سازنده", "owner", "فروشنده", "مالک"):
            updates["owner"] = val

        else:
            updates.setdefault("description", "")
            if updates["description"]:
                updates["description"] += "\n"
            updates["description"] += f"{key}: {val}"

    # اطمینان از اینکه countries و hashtags همیشه لیست هستند
    if "country" in updates and isinstance(updates["country"], str):
        updates["country"] = [c.strip() for c in re.split(r'[,\s]+', updates["country"]) if c.strip()]

    if "hashtags" in updates and isinstance(updates["hashtags"], str):
        updates["hashtags"] = [t.strip() for t in updates["hashtags"].split() if t.strip()]

    return updates


async def handle_new_shop_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new shop item image upload during editing"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})

    if user_data.get("step") != "awaiting_new_shop_image":
        return False

    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return True

    item_id = user_data.get("editing_shop_item_id")
    if not item_id:
        await update.message.reply_text("❌ خطا در شناسایی آیتم.")
        return True

    # Get new photo file_id
    new_photo_id = update.message.photo[-1].file_id

    try:
        from shop_handler import update_shop_item
        success = update_shop_item(item_id, {"photo_file_id": new_photo_id})

        if success:
            await update.message.reply_text(
                "✅ تصویر آیتم با موفقیت به‌روزرسانی شد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_view_shop_items")
                ]])
            )
        else:
            await update.message.reply_text("❌ خطا در به‌روزرسانی تصویر.")

        # Clear editing state
        context.user_data[user_id]["step"] = None
        context.user_data[user_id]["editing_shop_item_id"] = None

    except Exception as e:
        logger.error(f"Error updating shop item image: {e}")
        await update.message.reply_text("❌ خطا در به‌روزرسانی تصویر.")

    return True

# async def handle_new_shop_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle new shop item caption (or multi-field edit) during editing"""
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     # فقط در صورتی که در مرحله ویرایش باشیم
#     if user_data.get("step") != "awaiting_new_shop_caption":
#         return False

#     item_id = user_data.get("editing_shop_item_id")
#     if not item_id:
#         await update.message.reply_text("❌ خطا: آیتم پیدا نشد (شناسه موجود نیست).")
#         return True

#     raw_text = update.message.text or ""
#     updates = parse_shop_item_text(raw_text)

#     if not updates:
#         await update.message.reply_text(
#             "❌ فرمت ورودی قابل شناسایی نبود.\n\n"
#             "مثال‌های قابل قبول:\n"
#             "1) فقط توضیحات: یک خط متن -> این به عنوان description ذخیره می‌شود.\n"
#             "2) چند خط کلید: مقدار:\n"
#             "   نام: شمشیر جادویی\n"
#             "   نوع: Weapon\n"
#             "   کشور: Persia\n"
#             "   قیمت: 32000\n"
#             "   مواد: آهن:50, چوب:10\n"
#             "   توضیحات: این شمشیر قوی است.\n"
#         )
#         return True

#     logger.info(f"Attempting update for item_id={item_id} with updates={updates}")

#     try:
#         from shop_handler import update_shop_item, load_shop_items

#         # کمک برای دیباگ: آیا آیتم در فایل موجود است؟
#         items = load_shop_items()
#         existing_ids = [it.get("id") for it in items]
#         found = None
#         for it in items:
#             if str(it.get("id")) == str(item_id):
#                 found = it
#                 break

#         if not found:
#             logger.warning(f"Item {item_id} not found. existing ids: {existing_ids}")
#             await update.message.reply_text("❌ خطا: آیتم مورد نظر در فایل فروشگاه یافت نشد.")
#             # پاک‌سازی وضعیت برای جلوگیری از لوپ (یا نگه دار اگر خواستی)
#             context.user_data[user_id]["step"] = None
#             context.user_data[user_id]["editing_shop_item_id"] = None
#             return True

#         success = update_shop_item(item_id, updates)

#         if success:
#             await update.message.reply_text(
#                 "✅ آیتم با موفقیت به‌روزرسانی شد.",
#                 reply_markup=InlineKeyboardMarkup([[
#                     InlineKeyboardButton("🔙 بازگشت", callback_data="admin_view_shop_items")
#                 ]])
#             )
#         else:
#             logger.error(f"update_shop_item returned False for id={item_id}. existing ids: {existing_ids}")
#             await update.message.reply_text("❌ خطا در به‌روزرسانی آیتم. لاگ‌ها را بررسی کنید.")

#     except Exception as e:
#         logger.exception(f"Exception while updating shop item {item_id}: {e}")
#         await update.message.reply_text("❌ خطای داخلی در به‌روزرسانی آیتم. لاگ سرور را بررسی کنید.")

#     # clear state
#     context.user_data[user_id]["step"] = None
#     context.user_data[user_id]["editing_shop_item_id"] = None
#     return True


async def handle_new_shop_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new shop item caption (or multi-field edit) during editing with default count"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})

    # فقط در صورتی که در مرحله ویرایش باشیم
    if user_data.get("step") != "awaiting_new_shop_caption":
        return False

    item_id = user_data.get("editing_shop_item_id")
    if not item_id:
        await update.message.reply_text("❌ خطا: آیتم پیدا نشد (شناسه موجود نیست).")
        return True

    raw_text = update.message.text or ""
    
    # مشخص کردن نوع آیتم فعلی (برای پشتیبانی از count پیش‌فرض)
    from shop_handler import load_shop_items
    items = load_shop_items()
    found = None
    for it in items:
        if str(it.get("id")) == str(item_id):
            found = it
            break
    if not found:
        await update.message.reply_text("❌ خطا: آیتم مورد نظر در فایل فروشگاه یافت نشد.")
        context.user_data[user_id]["step"] = None
        context.user_data[user_id]["editing_shop_item_id"] = None
        return True

    item_type = found.get("type", "").lower()

    from shop_handler import update_shop_item
    updates = parse_shop_item_text(raw_text)

    # اگر نوع آیتم misc، weapons، castle یا structures باشد و count وارد نشده باشد، مقدار پیش‌فرض 1 بده
    if item_type in ("misc", "weapons", "castle", "structures") and "count" not in updates:
        updates["count"] = 1

    if not updates:
        await update.message.reply_text(
            "❌ فرمت ورودی قابل شناسایی نبود.\n\n"
            "مثال‌های قابل قبول:\n"
            "1) فقط توضیحات: یک خط متن -> این به عنوان description ذخیره می‌شود.\n"
            "2) چند خط کلید: مقدار:\n"
            "   نام: شمشیر جادویی\n"
            "   نوع: Weapon\n"
            "   کشور: Persia\n"
            "   قیمت: 32000\n"
            "   مواد: آهن:50, چوب:10\n"
            "   توضیحات: این شمشیر قوی است.\n"
        )
        return True

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting update for item_id={item_id} with updates={updates}")

    try:
        success = update_shop_item(item_id, updates)

        if success:
            await update.message.reply_text(
                "✅ آیتم با موفقیت به‌روزرسانی شد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="admin_view_shop_items")
                ]])
            )
        else:
            logger.error(f"update_shop_item returned False for id={item_id}")
            await update.message.reply_text("❌ خطا در به‌روزرسانی آیتم. لاگ‌ها را بررسی کنید.")

    except Exception as e:
        logger.exception(f"Exception while updating shop item {item_id}: {e}")
        await update.message.reply_text("❌ خطای داخلی در به‌روزرسانی آیتم. لاگ سرور را بررسی کنید.")

    # پاکسازی وضعیت
    context.user_data[user_id]["step"] = None
    context.user_data[user_id]["editing_shop_item_id"] = None
    return True



# Weekly Processing Functions
async def show_weekly_processing_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly processing options for admin"""
    query = update.callback_query
    await query.answer()

    text = "🔄 پردازش هفتگی استان‌ها"

    keyboard = [
        [InlineKeyboardButton("⚡ اجرای پردازش هفتگی", callback_data="run_weekly_processing")],
        [InlineKeyboardButton("📊 نمایش پیش‌بینی", callback_data="preview_weekly_processing")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_province_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


def calculate_weekly_income(province_data):
    """Calculate weekly income from mines"""
    mines = province_data.get("mines", {})
    mine_weekly_income = {
        "Stone mine": 2000,
        "Tin mine": 3000,
        "Iron mine": 5000,
        "Coal mine": 8000,
        "Copper mine": 10000,
        "Silver mine": 25000,
        "Golden mine": 50000,
        "Diamond mine": 100000,
    }
    total_income = 0
    details = []

    for mine_name, count in mines.items():
        if count > 0:
            income_per_mine = mine_weekly_income.get(mine_name, 0)
            mine_income = count * income_per_mine
            total_income += mine_income
            details.append(f"  • {mine_name}: {count} × {income_per_mine:,} = {mine_income:,}")

    return total_income, details




def calculate_tax_income(province_data):
    """Calculate weekly income from tax"""
    tax_rate = province_data.get("tax", 0)
    # هر 10 واحد مالیات 1,000 پول میده
    tax_income = (tax_rate // 10) * 1000
    return tax_income

def safe_load_json(path):
    if not os.path.isfile(path):
        print(f"⚠ فایل پیدا نشد: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# def apply_food_consumption(province_name):
#     econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
#     province_file = os.path.join(PROVINCE_FOLDER, province_name.replace(" ", "_") + ".json")

#     econ_data = safe_load_json(econ_file)
#     province_data = safe_load_json(province_file)
#     if not econ_data or not province_data:
#         return

#         # گرفتن جمعیت واقعی از فایل استان
#     population = province_data.get("population", 0)

#     grain_priority = econ_data.get("grain_priority", [])
#     grain_settings = econ_data.get("grains", {})

#         # گرفتن موجودی استان
#     items = province_data.get("economic_items", {})

#     remaining_population = population  # جمعیتی که هنوز باید براش غذا تأمین بشه

#     for grain in grain_priority:
#         if grain not in BASE_CONSUMPTION_RATES or grain not in items:
#             continue

#         base_people, base_amount = BASE_CONSUMPTION_RATES[grain]
#         percent = max(0, grain_settings.get(grain, 0))
#         multiplier = 1 + (percent / 100)

#             # مقدار مصرف برای هر نفر از این غله
#         units_per_person = (base_amount / base_people) * multiplier

#             # چقدر می‌تونیم از این غله تامین کنیم؟
#         available_units = items[grain]
#         max_people_supported = available_units / units_per_person

#         if max_people_supported >= remaining_population:
#                 # همه جمعیت را میشه ساپورت کرد
#             items[grain] -= remaining_population * units_per_person
#             remaining_population = 0
#             break  # نیاز برطرف شده
#         else:
#                 # فقط بخشی از جمعیت را میشه ساپورت کرد
#             items[grain] = 0
#             remaining_population -= int(max_people_supported)

#         # اگر هنوز جمعیت باقی مانده که غذا نگرفته‌اند، در econ_data ذخیره کن
#     econ_data["unfed_population"] = int(remaining_population)

#         # ذخیره تغییرات
#     save_json(province_file, province_data)
#     save_json(econ_file, econ_data)

#     print(f"✅ {province_name}: مصرف اعمال شد. باقی‌مانده گرسنه: {remaining_population}")


def apply_food_consumption(province_name):
    econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
    province_file = os.path.join(PROVINCE_FOLDER, province_name.replace(" ", "_") + ".json")

    econ_data = safe_load_json(econ_file)
    province_data = safe_load_json(province_file)
    if not econ_data or not province_data:
        return

    # گرفتن جمعیت واقعی از فایل استان
    population = province_data.get("population", 0)

    grain_priority = econ_data.get("grain_priority", [])
    grain_consumption = econ_data.get("grain_consumption", 0)  # 🔹 درصد کلی

    # گرفتن موجودی استان
    items = province_data.get("economic_items", {})

    remaining_population = population  # جمعیتی که هنوز باید براش غذا تأمین بشه

    for grain in grain_priority:
        if grain not in BASE_CONSUMPTION_RATES or grain not in items:
            continue

        base_people, base_amount = BASE_CONSUMPTION_RATES[grain]

        # 🔹 درصد کلی برای همه غلات اعمال میشه
        multiplier = 1 + (grain_consumption / 100)

        # مقدار مصرف برای هر نفر از این غله
        units_per_person = (base_amount / base_people) * multiplier

        # چقدر می‌تونیم از این غله تامین کنیم؟
        available_units = items[grain]
        max_people_supported = available_units / units_per_person

        if max_people_supported >= remaining_population:
            # همه جمعیت را میشه ساپورت کرد
            items[grain] -= remaining_population * units_per_person
            remaining_population = 0
            break  # نیاز برطرف شده
        else:
            # فقط بخشی از جمعیت را میشه ساپورت کرد
            items[grain] = 0
            remaining_population -= int(max_people_supported)

    # اگر هنوز جمعیت باقی مانده که غذا نگرفته‌اند، در econ_data ذخیره کن
    econ_data["unfed_population"] = int(remaining_population)

    # ذخیره تغییرات
    save_json(province_file, province_data)
    save_json(econ_file, econ_data)

    print(f"✅ {province_name}: مصرف اعمال شد. باقی‌مانده گرسنه: {remaining_population}")



def calculate_weekly_production(province_data):
    """Calculate weekly production from economic structures"""
    structures = province_data.get("economic_structures", {})

    production_results = {}
    details = []

    for struct_name, struct_info in structures.items():
        count = struct_info.get("count", 0)
        product = struct_info.get("product", "")
        weekly_output = struct_info.get("weekly_output", 0)

        if product and weekly_output > 0:
            total_production = count * weekly_output
            production_results[product] = production_results.get(product, 0) + total_production
            details.append(f"  • {struct_name}: {count} × {weekly_output} = {total_production} {product}")

    return production_results, details


def calculate_popularity_effect(province_data, is_capital=False):
    tax_rate = province_data.get("tax", 0)
    popularity_change = 0
    if is_capital:
        if tax_rate > 0:
            popularity_change = -(tax_rate // 10)
    else:
        if tax_rate > 10:
            popularity_change = -((tax_rate - 10) // 10)
    return popularity_change


async def preview_weekly_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Preview weekly processing results"""
    query = update.callback_query
    await query.answer()

    try:
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        text = "📊 پیش‌بینی پردازش هفتگی:\n\n"

        for country, provinces in countries_data.get("countries_areas", {}).items():
            text += f"🌍 {country}:\n"

            for province in provinces:
                province_data = load_province_data(country, province)
                if not province_data:
                    continue

                # محاسبه درآمد معدن
                mine_income, mine_details = calculate_weekly_income(province_data)

                # محاسبه درآمد مالیات
                tax_income = calculate_tax_income(province_data)

                # جمع کل درآمد ثروت
                total_income = mine_income + tax_income

                # محاسبه تولیدات اقتصادی
                production_results, prod_details = calculate_weekly_production(province_data)

                # محاسبه محبوبیت
                popularity_change = calculate_tax_popularity(province)

                # اول اسم استان را بنویس
                text += f"  📍 {province}:\n\n"

                # پیش‌بینی مصرف غذا بعد از اسم استان
                food_preview = preview_food_consumption(province)
                if food_preview:
                    text += "    🍽️ مصرف غلات:\n\n"
                    for line in food_preview:
                        text += f"      • {line}\n"

                if mine_details:
                    text += "\n    💎 درآمد معدن:\n"
                    for d in mine_details:
                        text += f"{d}\n"

                if tax_income > 0:
                    text += f"\n    🏛️ درآمد مالیات: +{tax_income:,}\n"

                if total_income > 0:
                    text += f"\n    💰 کل درآمد: +{total_income:,}\n"

                if production_results:
                    text += "\n    📦 تولیدات اقتصادی:\n"
                    for item, amount in production_results.items():
                        text += f"      • {item}: +{amount:,}\n"

                tax_popularity_change = calculate_tax_popularity(province)
                hunger_consumption_change = calculate_hunger_and_consumption_popularity(province)
                
                text += "\n📊 تغییرات محبوبیت:\n"
                
                # بخش مالیات
                if tax_popularity_change != 0:
                    change_str = f"+{tax_popularity_change}" if tax_popularity_change > 0 else str(tax_popularity_change)
                    text += f"  • {change_str} (مالیات)\n"
                else:
                    text += "  • 0 (مالیات)\n"
                
                # بخش مصرف غلات
                if hunger_consumption_change != 0:
                    change_str = f"+{hunger_consumption_change}" if hunger_consumption_change > 0 else str(hunger_consumption_change)
                    text += f"  • {change_str} (مصرف غلات/ضریب مصرف)\n"
                else:
                    text += "  • 0 (مصرف غلات/ضریب مصرف)\n"



                text += "\n"

            text += "\n"

        keyboard = [
            [InlineKeyboardButton("🥖 اجرای غلات", callback_data="run_food_processing")],
            [InlineKeyboardButton("⚡ اجرا", callback_data="run_weekly_processing")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="show_weekly_menu")]
        ]

        MAX_LENGTH = 4000
        chunks = [text[i:i+MAX_LENGTH] for i in range(0, len(text), MAX_LENGTH)]

        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                # آخرین بخش: با دکمه‌ها
                await query.message.reply_text(chunk, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                # سایر بخش‌ها بدون دکمه
                await query.message.reply_text(chunk)

    except Exception as e:
        logger.error(f"❌ خطا در پیش‌بینی هفتگی: {e}")
        await query.edit_message_text("❌ خطا در محاسبه پیش‌بینی")





# async def run_food_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     try:
#         # مرحله اول: بررسی زمان آخرین تیک غذا
#         timers = safe_load_json("timers.json")
#         if not timers:
#             await query.edit_message_text("❌ خطا در بارگذاری فایل زمان‌بندی.")
#             return

#         last_tick_str = timers.get("last_food_tick")
#         if not last_tick_str:
#             await query.edit_message_text("❌ زمان آخرین مصرف غذا مشخص نیست.")
#             return

#         last_tick = datetime.fromisoformat(last_tick_str)
#         now = datetime.now()

#         if (now - last_tick).days < 8:
#             await query.edit_message_text("⏳ هنوز ۸ روز از آخرین مصرف غذا نگذشته.")
#             return

#         # مرحله دوم: بارگذاری داده‌های کشورها
#         data = safe_load_json(COUNTRIES_FILE)
#         if not data:
#             await query.edit_message_text("❌ خطا در بارگذاری داده کشورها")
#             return

#         for country, provinces in data.get("countries_areas", {}).items():
#             for province_name in provinces:
#                 econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
#                 country_name = find_country_for_province(province_name)
#                 if not country_name:
#                     continue

#                 province_filename = f"{country_name}_{province_name}".replace(" ", "_") + ".json"
#                 province_file = os.path.join(PROVINCE_FOLDER, province_filename)
                
#                 province_data = safe_load_json(province_file)
#                 econ_data = safe_load_json(econ_file)
#                 if not province_data or not econ_data:
#                     continue
                
#                 # ───── تغییر محبوبیت شنبه (گرسنگی + ضریب مصرف) ─────
#                 hunger_consumption_popularity = calculate_hunger_and_consumption_popularity(province_name)
#                 province_data["popularity"] = province_data.get("popularity", 0) + hunger_consumption_popularity


#                 population = province_data.get("population", 0)
#                 grain_priority = econ_data.get("grain_priority", [])
#                 grain_settings = econ_data.get("grains", {})
#                 items = province_data.get("economic_items", {})

#                 remaining_population = population

#                 for grain in grain_priority:
#                     if grain not in BASE_CONSUMPTION_RATES or grain not in items:
#                         continue

#                     base_people, base_amount = BASE_CONSUMPTION_RATES[grain]
#                     percent = max(0, grain_settings.get(grain, 0))
#                     multiplier = 1 + (percent / 100)
#                     units_per_person = (base_amount / base_people) * multiplier
#                     available_units = items.get(grain, 0)

#                     max_people_supported = available_units / units_per_person

#                     if max_people_supported >= remaining_population:
#                         items[grain] -= remaining_population * units_per_person
#                         remaining_population = 0
#                         break
#                     else:
#                         items[grain] = 0
#                         remaining_population -= int(max_people_supported)

#                 province_data["economic_items"] = items
#                 with open(province_file, "w", encoding="utf-8") as f:
#                     json.dump(province_data, f, ensure_ascii=False, indent=2)

#         # مرحله سوم: به‌روزرسانی زمان مصرف غذا
#         timers["last_food_tick"] = now.isoformat()
#         with open("timers.json", "w", encoding="utf-8") as f:
#             json.dump(timers, f, ensure_ascii=False, indent=2)

#         await query.edit_message_text("✅ مصرف غذا برای همه استان‌ها اعمال شد (۸ روزه).")

#     except Exception as e:
#         logger.error(f"❌ خطا در اجرای مصرف غذا: {e}")
#         await query.edit_message_text("❌ خطا در اجرای مصرف غذا")

async def run_food_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # مرحله اول: بررسی زمان آخرین تیک غذا
        timers = safe_load_json("timers.json")
        if not timers:
            await query.edit_message_text("❌ خطا در بارگذاری فایل زمان‌بندی.")
            return

        last_tick_str = timers.get("last_food_tick")
        if not last_tick_str:
            await query.edit_message_text("❌ زمان آخرین مصرف غذا مشخص نیست.")
            return

        last_tick = datetime.fromisoformat(last_tick_str)
        now = datetime.now()

        if (now - last_tick).days < 8:
            await query.edit_message_text("⏳ هنوز ۸ روز از آخرین مصرف غذا نگذشته.")
            return

        # مرحله دوم: بارگذاری داده‌های کشورها
        data = safe_load_json(COUNTRIES_FILE)
        if not data:
            await query.edit_message_text("❌ خطا در بارگذاری داده کشورها")
            return

        for country, provinces in data.get("countries_areas", {}).items():
            for province_name in provinces:
                econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
                country_name = find_country_for_province(province_name)
                if not country_name:
                    continue

                province_filename = f"{country_name}_{province_name}".replace(" ", "_") + ".json"
                province_file = os.path.join(PROVINCE_FOLDER, province_filename)
                
                province_data = safe_load_json(province_file)
                econ_data = safe_load_json(econ_file)
                if not province_data or not econ_data:
                    continue
                
                # ───── تغییر محبوبیت شنبه (گرسنگی + ضریب مصرف) ─────
                hunger_consumption_popularity = calculate_hunger_and_consumption_popularity(province_name)
                # province_data["popularity"] = province_data.get("popularity", 0) + hunger_consumption_popularity
                check = province_data.get("popularity", 0) + hunger_consumption_popularity
                if check > 100:
                    province_data["popularity"] = 100
                else:
                    province_data["popularity"] = check

                # مصرف غذا
                population = province_data.get("population", 0)
                grain_priority = econ_data.get("grain_priority", [])
                grain_consumption = econ_data.get("grain_consumption", 0)  # 🔹 درصد کلی
                items = province_data.get("economic_items", {})

                remaining_population = population

                for grain in grain_priority:
                    if grain not in BASE_CONSUMPTION_RATES or grain not in items:
                        continue

                    base_people, base_amount = BASE_CONSUMPTION_RATES[grain]

                    # 🔹 ضریب کلی روی همه غلات اعمال میشه
                    multiplier = 1 + (grain_consumption / 100)

                    units_per_person = (base_amount / base_people) * multiplier
                    available_units = items.get(grain, 0)

                    max_people_supported = available_units / units_per_person

                    if max_people_supported >= remaining_population:
                        items[grain] -= remaining_population * units_per_person
                        remaining_population = 0
                        break
                    else:
                        items[grain] = 0
                        remaining_population -= int(max_people_supported)

                province_data["economic_items"] = items

                with open(province_file, "w", encoding="utf-8") as f:
                    json.dump(province_data, f, ensure_ascii=False, indent=2)

                # ✅ گرسنه‌ها رو هم تو econ ذخیره کنیم (برای استفاده بعدی)
                econ_data["unfed_population"] = int(remaining_population)
                with open(econ_file, "w", encoding="utf-8") as f:
                    json.dump(econ_data, f, ensure_ascii=False, indent=2)

        # مرحله سوم: به‌روزرسانی زمان مصرف غذا
        timers["last_food_tick"] = now.isoformat()
        with open("timers.json", "w", encoding="utf-8") as f:
            json.dump(timers, f, ensure_ascii=False, indent=2)

        await query.edit_message_text("✅ مصرف غذا برای همه استان‌ها اعمال شد (۸ روزه).")

    except Exception as e:
        logger.error(f"❌ خطا در اجرای مصرف غذا: {e}")
        await query.edit_message_text("❌ خطا در اجرای مصرف غذا")



async def run_weekly_processing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        # ۱. بارگذاری timers.json و چک کردن زمان آخرین اجرای هفتگی
        if not os.path.exists(TIMERS_FILE):
            await query.edit_message_text("❌ فایل زمان‌بندی یافت نشد.")
            return

        with open(TIMERS_FILE, "r", encoding="utf-8") as f:
            timers = json.load(f)

        last_update_str = timers.get("last_weekly_update")
        if not last_update_str:
            await query.edit_message_text("❌ زمان آخرین به‌روزرسانی هفتگی مشخص نیست.")
            return

        last_update = datetime.fromisoformat(last_update_str)
        now = datetime.now()

        if (now - last_update).days < 7:
            await query.edit_message_text("⏳ هنوز ۷ روز از آخرین پردازش هفتگی نگذشته است.")
            return

        # ۲. بارگذاری اطلاعات کشورها
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        processed_count = 0
        total_wealth_added = 0

        for country, provinces in countries_data.get("countries_areas", {}).items():
            for province in provinces:
                province_data = load_province_data(country, province)
                if not province_data:
                    continue

                # محاسبه درآمدها
                mine_income, _ = calculate_weekly_income(province_data)
                tax_income = calculate_tax_income(province_data)
                income = mine_income + tax_income
                province_data["wealth"] = province_data.get("wealth", 0) + income
                total_wealth_added += income

                # محاسبه تولیدات اقتصادی
                production_results, _ = calculate_weekly_production(province_data)
                if production_results:
                    if "economic_items" not in province_data:
                        province_data["economic_items"] = {}
                    for item, amount in production_results.items():
                        current = province_data["economic_items"].get(item, 0)
                        province_data["economic_items"][item] = current + amount

                # محاسبه محبوبیت
                popularity_change = calculate_tax_popularity(province)
                province_data["popularity"] = province_data.get("popularity", 50) + popularity_change

                # ذخیره داده استان
                save_province_data(country, province, province_data)
                processed_count += 1

        # ۳. به‌روزرسانی زمان آخرین پردازش هفتگی در timers.json
        timers["last_weekly_update"] = now.isoformat()
        with open(TIMERS_FILE, "w", encoding="utf-8") as f:
            json.dump(timers, f, ensure_ascii=False, indent=2)

        text = (
            f"✅ پردازش هفتگی کامل شد!\n\n"
            f"📊 آمار:\n"
            f"• استان‌های پردازش شده: {processed_count}\n"
            f"• کل ثروت اضافه شده: {total_wealth_added:,}\n"
            f"• تاریخ پردازش: {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"• زمان پردازش بعدی: {(now + timedelta(days=7)).strftime('%Y-%m-%d %H:%M')}"
        )

        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="show_weekly_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"❌ خطا در اجرای پردازش هفتگی: {e}")
        await query.edit_message_text("❌ خطا در اجرای پردازش هفتگی")


# async def generate_shop_item_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Generate and save shop item to JSON file"""
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     item_data = user_data.get("shop_item_data", {})

#     try:
#         photo = item_data["photo"]
#         name = item_data["name"]
#         item_type = item_data["type"]
#         countries = item_data.get("countries", [])  # لیست کشورها
#         description = item_data["description"]
#         price_materials = item_data["price"]
#         owner_id = item_data.get("owner_id", "-")
#         count = item_data.get("count", None)

#         # تجزیه قیمت و مواد
#         price = 0
#         materials = {}

#         parts = price_materials.split(",")
#         if parts:
#             try:
#                 price = int(parts[0].strip())
#             except ValueError:
#                 price = 0

#             for part in parts[1:]:
#                 if ":" in part:
#                     mat_name, mat_amount = part.split(":", 1)
#                     try:
#                         materials[mat_name.strip()] = int(mat_amount.strip())
#                     except ValueError:
#                         continue

#         # حذف تکرار هشتگ‌ها و ایجاد لیست کامل هشتگ‌ها
#         all_hashtags = [f"#{item_type}"] + [f"#{c}" for c in countries] + [h for h in item_data.get("hashtags", [])]
#         hashtags = list(dict.fromkeys(all_hashtags))  # حذف تکرار و حفظ ترتیب

#         # افزودن تعداد به توضیحات در صورت وجود و نوع ارتش
#         if count is not None and item_type.lower() == "army":
#             description += f", تعداد: {count}"

#         # ساخت آیتم جدید
#         new_item = {
#             "name": name,
#             "type": item_type,
#             "countries": countries,
#             "description": description,
#             "price": price,
#             "materials": materials,
#             "owner": owner_id,
#             "hashtags": hashtags,
#             "photo_file_id": photo,
#             "count": count if count is not None else 1
#         }

#         # ذخیره در فایل
#         from shop_handler import add_shop_item
#         item_id = add_shop_item(new_item)

#         # ارسال به کانال
#         try:
#             caption = f"""──────⊱◈Shop◈⊰──────
# ✦ Item Name : {name}
# ✧ Item Type : {item_type}
# ✦ Countries : {', '.join(countries)}
# {' '.join(hashtags)}
# ✧ Description :
# • {description}
# ✦ Price & Materials :
# • {price_materials}
# ✧ Owner ID : {owner_id}
# ──────⊹⊱✫⊰⊹──────
# https://t.me/R_O_T_C
# https://t.me/R_O_T_C_Shop"""

#             await context.bot.send_photo(
#                 chat_id=SHOP_CHANNEL,
#                 photo=photo,
#                 caption=caption
#             )
#         except Exception as channel_error:
#             logger.warning(f"Could not send to channel: {channel_error}")

#         await update.message.reply_text(
#             f"✅ آیتم با موفقیت به فروشگاه اضافه شد!\n🆔 شناسه آیتم: {item_id}",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")
#             ]])
#         )

#         # پاک کردن داده‌های کاربر
#         context.user_data[user_id] = {}

#     except Exception as e:
#         logger.error(f"Error generating shop item: {e}")
#         await update.message.reply_text(
#             f"❌ خطا در ایجاد آیتم: {str(e)}",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")
#             ]])
#         )


async def generate_shop_item_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and save shop item to JSON file with proper count handling"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    item_data = user_data.get("shop_item_data", {})

    try:
        photo = item_data["photo"]
        name = item_data["name"]
        item_type = item_data["type"]
        countries = item_data.get("countries", [])  # لیست کشورها
        description = item_data["description"]
        price_materials = item_data["price"]
        owner_id = item_data.get("owner_id", "-")
        count = item_data.get("count", 1)  # پیش‌فرض 1

        # تجزیه قیمت و مواد
        price = 0
        materials = {}

        parts = price_materials.split(",") if price_materials else []
        if parts:
            try:
                price = int(parts[0].strip())
            except ValueError:
                price = 0

            for part in parts[1:]:
                if ":" in part:
                    mat_name, mat_amount = part.split(":", 1)
                    try:
                        materials[mat_name.strip()] = int(mat_amount.strip())
                    except ValueError:
                        continue

        # حذف تکرار هشتگ‌ها و ایجاد لیست کامل هشتگ‌ها
        all_hashtags = [f"#{item_type}"] + [f"#{c}" for c in countries] + [h for h in item_data.get("hashtags", [])]
        hashtags = list(dict.fromkeys(all_hashtags))  # حذف تکرار و حفظ ترتیب

        # افزودن تعداد به توضیحات در صورت وجود و برای آیتم‌های مرتبط
        if count is not None and item_type.lower() in ("army", "misc", "weapons", "castle", "structure"):
            description += f", تعداد: {count}"

        # ساخت آیتم جدید
        new_item = {
            "name": name,
            "type": item_type,
            "countries": countries,
            "description": description,
            "price": price,
            "materials": materials,
            "owner": owner_id,
            "hashtags": hashtags,
            "photo_file_id": photo,
            "count": count if count is not None else 1  # همیشه یک عدد داشته باشه
        }

        # ذخیره در فایل
        from shop_handler import add_shop_item
        item_id = add_shop_item(new_item)

        # ارسال به کانال
        try:
            caption = f"""──────⊱◈Shop◈⊰──────
✦ Item Name : {name}
✧ Item Type : {item_type}
✦ Countries : {', '.join(countries)}
{' '.join(hashtags)}
✧ Description :
• {description}
✦ Price & Materials :
• {price_materials}
✧ Owner ID : {owner_id}
──────⊹⊱✫⊰⊹──────
https://t.me/R_O_T_C
https://t.me/R_O_T_C_Shop"""

            await context.bot.send_photo(
                chat_id=SHOP_CHANNEL,
                photo=photo,
                caption=caption
            )
        except Exception as channel_error:
            logger.warning(f"Could not send to channel: {channel_error}")

        await update.message.reply_text(
            f"✅ آیتم با موفقیت به فروشگاه اضافه شد!\n🆔 شناسه آیتم: {item_id}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")
            ]])
        )

        # پاک کردن داده‌های کاربر
        context.user_data[user_id] = {}

    except Exception as e:
        logger.error(f"Error generating shop item: {e}")
        await update.message.reply_text(
            f"❌ خطا در ایجاد آیتم: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")
            ]])
        )



async def admin_view_shop_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin function to view all shop items"""
    query = update.callback_query
    await query.answer()

    try:
        from shop_handler import load_shop_items

        # Load items from JSON file
        shop_items = load_shop_items()

        if not shop_items:
            await query.edit_message_text(
                "📭 هیچ آیتمی در فروشگاه یافت نشد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 برگشت", callback_data="admin_manage_shop")
                ]])
            )
            return

        # Store items for navigation
        user_id = query.from_user.id
        context.user_data[user_id] = context.user_data.get(user_id, {})
        context.user_data[user_id]["admin_shop_items"] = shop_items
        context.user_data[user_id]["admin_shop_page"] = 0

        await show_admin_shop_page_internal(query, context, user_id, 0)

    except Exception as e:
        logger.error(f"Error viewing shop items: {e}")
        await query.edit_message_text(
            "❌ خطا در نمایش آیتم‌های فروشگاه.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 برگشت", callback_data="admin_manage_shop")
            ]])
        )

async def show_admin_shop_page_internal(query, context, user_id, page):
    """Show admin shop items with navigation and management buttons"""
    user_data = context.user_data.get(user_id, {})
    items = user_data.get("admin_shop_items", [])

    if not items:
        await query.edit_message_text(
            "📭 هیچ آیتمی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="admin_manage_shop")
            ]])
        )
        return

    # total_pages = len(items)
    # page = max(0, min(page, total_pages - 1))
    # current_item = items[page]

    # # Format item display for admin
    # text = f"👑 مدیریت فروشگاه - آیتم {page + 1} از {total_pages}\n\n"
    # text += f"📦 {current_item['name']}\n\n"
    # text += f"🏷 نوع: {current_item['type']}\n"
    # text += f"🌍 کشور: {current_item['country']}\n"
    # text += f"💰 قیمت: {current_item['price']:,} طلا\n"
    total_pages = len(items)
    page = max(0, min(page, total_pages - 1))
    current_item = items[page]
    
    # Format item display for admin
    text = f"👑 مدیریت فروشگاه - آیتم {page + 1} از {total_pages}\n\n"
    text += f"📦 {current_item.get('name', 'نامشخص')}\n\n"
    text += f"🏷 نوع: {current_item.get('type', 'نامشخص')}\n"
    
    # نمایش کشورها به صورت لیست یا رشته
    countries_list = current_item.get('countries')
    country_single = current_item.get('country')
    
    if countries_list and isinstance(countries_list, list) and len(countries_list) > 0:
        countries_str = ', '.join(countries_list)
    elif country_single:
        countries_str = country_single
    else:
        countries_str = 'نامشخص'
    
    text += f"🌍 کشورها: {countries_str}\n"
    
    text += f"💰 قیمت: {current_item.get('price', 0):,} طلا\n"


    if current_item.get('materials'):
        text += "\n🔧 مواد مورد نیاز:\n"
        for material, amount in current_item['materials'].items():
            text += f"   • {material}: {amount:,}\n"

    if current_item.get('description'):
        text += f"\n📝 توضیحات:\n{current_item['description']}\n"

    if current_item.get('hashtags'):
        text += f"\n🏷️ برچسب‌ها: {' '.join(current_item['hashtags'])}\n"

    text += f"\n👤 فروشنده: {current_item.get('owner', 'نامشخص')}"
    text += f"\n🆔 آیتم ID: {current_item.get('id', 'N/A')}"

    if current_item.get('created_at'):
        text += f"\n📅 تاریخ ایجاد: {current_item['created_at'][:19].replace('T', ' ')}"

    # Navigation buttons
    nav_buttons = []
    if total_pages > 1:
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_shop_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_shop_page_{page+1}"))

    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Edit and Delete buttons
    item_id = current_item.get('id', 'N/A')
    if item_id != 'N/A':
        keyboard.append([
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"admin_edit_shop_item_{item_id}"),
            InlineKeyboardButton("🗑️ حذف", callback_data=f"admin_delete_shop_item_{item_id}")
        ])
        logger.info(f"🔘 دکمه ویرایش ساخته شد با callback_data: admin_edit_shop_item_{item_id}")

    # Fixed back button that returns to Store Management menu
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_province_menu")])

    # Try to display with photo if available
    photo_file_id = current_item.get('photo_file_id')

    try:
        if photo_file_id:
            try:
                await query.delete_message()
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_file_id,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except Exception as photo_error:
                logger.error(f"Error sending admin photo: {photo_error}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    except Exception as e:
        logger.error(f"Error displaying admin item: {e}")
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    

async def show_admin_shop_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # استخراج شماره صفحه از callback_data
    data = query.data  # مثلا "admin_shop_page_2"
    page_str = data.split("_")[-1]
    try:
        page = int(page_str)
    except ValueError:
        page = 0

    await show_admin_shop_page_internal(query, context, user_id, page)


def find_country_for_province(province_name, countries_file="countries.json"):
    with open(countries_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    countries_areas = data.get("countries_areas", {})
    for country, provinces in countries_areas.items():
        if province_name in provinces:
            return country
    return None


# def preview_food_consumption(province_name):
#     # econ_file فقط اسم استان
#     econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")

#     # برای province_file اول کشور رو پیدا می‌کنیم
#     country_name = find_country_for_province(province_name)
#     if not country_name:
#         return None

#     province_filename = f"{country_name}_{province_name}".replace(" ", "_") + ".json"
#     province_file = os.path.join(PROVINCE_FOLDER, province_filename)

#     econ_data = safe_load_json(econ_file)
#     province_data = safe_load_json(province_file)
#     if not econ_data or not province_data:
#         return None

#     population = province_data.get("population", 0)
#     grain_priority = econ_data.get("grain_priority", [])
#     grain_settings = econ_data.get("grains", {})
#     items = province_data.get("economic_items", {}).copy()  # کپی برای جلوگیری از تغییر
#     remaining_population = population

#     consumption_result = []

#     for grain in grain_priority:
#         if grain not in BASE_CONSUMPTION_RATES or grain not in items:
#             continue

#         base_people, base_amount = BASE_CONSUMPTION_RATES[grain]
#         percent = max(0, grain_settings.get(grain, 0))
#         multiplier = 1 + (percent / 100)
#         units_per_person = (base_amount / base_people) * multiplier
#         available_units = items[grain]
#         max_people_supported = available_units / units_per_person

#         if max_people_supported >= remaining_population:
#             consumption_result.append(f"🍞 {grain}: تامین کامل ({remaining_population} نفر)")
#             remaining_population = 0
#             break
#         else:
#             consumption_result.append(f"🍞 {grain}: تامین ناقص ({int(max_people_supported)} نفر)")
#             remaining_population -= int(max_people_supported)

#     if remaining_population > 0:
#         consumption_result.append(f"⚠️ جمعیت گرسنه: {int(remaining_population)} نفر")
#     else:
#         consumption_result.append("✅ تمام جمعیت غذا دریافت کردند")

#     return consumption_result


def preview_food_consumption(province_name):
    # econ_file فقط اسم استان
    econ_file = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")

    # برای province_file اول کشور رو پیدا می‌کنیم
    country_name = find_country_for_province(province_name)
    if not country_name:
        return None

    province_filename = f"{country_name}_{province_name}".replace(" ", "_") + ".json"
    province_file = os.path.join(PROVINCE_FOLDER, province_filename)

    econ_data = safe_load_json(econ_file)
    province_data = safe_load_json(province_file)
    if not econ_data or not province_data:
        return None

    population = province_data.get("population", 0)
    grain_priority = econ_data.get("grain_priority", [])
    grain_consumption = econ_data.get("grain_consumption", 0)  # 🔹 درصد کلی
    items = province_data.get("economic_items", {}).copy()  # کپی برای جلوگیری از تغییر
    remaining_population = population

    consumption_result = []

    for grain in grain_priority:
        if grain not in BASE_CONSUMPTION_RATES or grain not in items:
            continue

        base_people, base_amount = BASE_CONSUMPTION_RATES[grain]

        # 🔹 ضریب کلی برای همه‌ی غلات
        multiplier = 1 + (grain_consumption / 100)

        units_per_person = (base_amount / base_people) * multiplier
        available_units = items[grain]
        max_people_supported = available_units / units_per_person

        if max_people_supported >= remaining_population:
            consumption_result.append(f"🍞 {grain}: تامین کامل ({remaining_population} نفر)")
            remaining_population = 0
            break
        else:
            consumption_result.append(f"🍞 {grain}: تامین ناقص ({int(max_people_supported)} نفر)")
            remaining_population -= int(max_people_supported)

    if remaining_population > 0:
        consumption_result.append(f"⚠️ جمعیت گرسنه: {int(remaining_population)} نفر")
    else:
        consumption_result.append("✅ تمام جمعیت غذا دریافت کردند")

    return consumption_result


# def calculate_province_popularity(province_name: str) -> int:
#     """Calculate total popularity change for a given province"""

#     # پایتخت‌ها و دوکنشین‌ها
#     CAPITALS = [
#         "Marevenport", "Eldhalm", "Verindel", "Trenhallough",
#         "Zahramun", "Lusauren", "Kalindora", "ShinrinkyAlkyanos", "Alkyanos"
#     ]
#     DUKEDOMS = ["Sea-Dragon", "Sky-Dragon", "Grand-Duke"]

#     # پیدا کردن کشور
#     country_name = find_country_for_province(province_name)
#     if not country_name:
#         return 0  # یا None اگه ترجیح بدی

#     province_filename = f"{country_name}_{province_name}".replace(" ", "_") + ".json"
#     province_path = os.path.join(PROVINCE_FOLDER, province_filename)
#     econ_path = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")

#     province_data = safe_load_json(province_path)
#     econ_data = safe_load_json(econ_path)

#     if not province_data or not econ_data:
#         return 0

#     total_popularity = 0

#     # ───── بخش 1: مالیات ─────
#     tax_rate = province_data.get("tax", 0)

#     if province_name in CAPITALS or province_name in DUKEDOMS:
#         tax_popularity = - (tax_rate // 10)
#     else:
#         tax_popularity = - max(0, (tax_rate - 10) // 10)

#     total_popularity += tax_popularity

#     # ───── بخش 2: جمعیت گرسنه ─────
#     population = province_data.get("population", 0)
#     grain_priority = econ_data.get("grain_priority", [])
#     grain_settings = econ_data.get("grains", {})
#     items = province_data.get("economic_items", {}).copy()
#     remaining_population = population

#     for grain in grain_priority:
#         if grain not in BASE_CONSUMPTION_RATES or grain not in items:
#             continue

#         base_people, base_amount = BASE_CONSUMPTION_RATES[grain]
#         percent = max(0, grain_settings.get(grain, 0))
#         multiplier = 1 + (percent / 100)
#         units_per_person = (base_amount / base_people) * multiplier
#         available_units = items.get(grain, 0)
#         max_people_supported = available_units / units_per_person

#         if max_people_supported >= remaining_population:
#             remaining_population = 0
#             break
#         else:
#             remaining_population -= int(max_people_supported)

#     if remaining_population > 0:
#         if remaining_population <= 1000:
#             hunger_penalty = -1
#         else:
#             hunger_penalty = - ((remaining_population // 1000)+1)
#         total_popularity += hunger_penalty

#     # ───── بخش 3: ضریب مصرف غذا ─────
#     for grain, percent in grain_settings.items():
#         bonus = percent // 50  # هر ۵۰ درصد = ۱ امتیاز
#         total_popularity += bonus

#     return total_popularity


def calculate_tax_popularity(province_name: str) -> int:
    """محاسبه تغییرات محبوبیت ناشی از مالیات (جمعه)"""
    country_name = find_country_for_province(province_name)
    if not country_name:
         return 0  # یا None اگه ترجیح بدی
    province_data = load_province_data(country_name,province_name)
    if not province_data:
        return 0

    tax_rate = province_data.get("tax", 0)
    CAPITALS = [
        "Marevenport", "Verindel", "Trenhallough",
         "Zahramun", "Lusauren", "Kalindora", "ShinrinkyAlkyanos", "Alkyanos"
     ]
    DUKEDOMS = ["Sea-Dragon", "Sky-Dragon", "Grand-Duke", "Guardian-of-Sharia", "King-of-wealth"]

    if province_name in CAPITALS or province_name in DUKEDOMS:
        return - (tax_rate // 10)
    return - max(0, (tax_rate - 10) // 10)

# def calculate_hunger_and_consumption_popularity(province_name: str) -> int:
#     """محاسبه تغییرات محبوبیت ناشی از گرسنگی و ضریب مصرف (شنبه)"""
#     country_name = find_country_for_province(province_name)
#     if not country_name:
#          return 0  # یا None اگه ترجیح بدی
#     province_data = load_province_data(country_name,province_name)
#     if not province_data:
#         return 0
   
#     econ_path = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
#     econ_data = safe_load_json(econ_path)
#     if not province_data or not econ_data:
#         return 0

#     population = province_data.get("population", 0)
#     grain_priority = econ_data.get("grain_priority", [])
#     grain_settings = econ_data.get("grains", {})
#     items = province_data.get("economic_items", {}).copy()
#     remaining_population = population

#     # بخش گرسنگی
#     for grain in grain_priority:
#         if grain not in BASE_CONSUMPTION_RATES or grain not in items:
#             continue

#         base_people, base_amount = BASE_CONSUMPTION_RATES[grain]
#         percent = max(0, grain_settings.get(grain, 0))
#         multiplier = 1 + (percent / 100)
#         units_per_person = (base_amount / base_people) * multiplier
#         available_units = items.get(grain, 0)
#         max_people_supported = available_units / units_per_person

#         if max_people_supported >= remaining_population:
#             remaining_population = 0
#             break
#         else:
#             remaining_population -= int(max_people_supported)

#     total = 0
#     if remaining_population > 0:
#         if remaining_population <= 1000:
#             total -= 1
#         else:
#             total -= (remaining_population // 1000) + 1

#     # بخش ضریب مصرف
#     for grain, percent in grain_settings.items():
#         total += percent // 50  # هر ۵۰٪ مصرف = +۱ محبوبیت

#     return total


# def calculate_hunger_and_consumption_popularity(province_name: str) -> int:
#     """محاسبه تغییرات محبوبیت ناشی از گرسنگی و ضریب مصرف (نسخه جدید تک‌درصدی)"""

#     # پیدا کردن کشور و بارگذاری داده‌ها
#     country_name = find_country_for_province(province_name)
#     if not country_name:
#         return 0
#     province_data = load_province_data(country_name, province_name)
#     if not province_data:
#         return 0

#     econ_path = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
#     econ_data = safe_load_json(econ_path)
#     if not econ_data:
#         return 0

#     # داده‌های اصلی
#     population = province_data.get("population", 0)
#     items = province_data.get("economic_items", {}).copy()
#     remaining_population = population

#     # درصد کلی مصرف غلات (پیش‌فرض 0 اگه نباشه)
#     grain_consumption = max(0, econ_data.get("grain_consumption", 0))

#     # ---------------- بخش گرسنگی ----------------
#     if "grains" in BASE_CONSUMPTION_RATES and "grains" in items:
#         base_people, base_amount = BASE_CONSUMPTION_RATES["grains"]

#         multiplier = 1 + (grain_consumption / 100)
#         units_per_person = (base_amount / base_people) * multiplier
#         available_units = items.get("grains", 0)
#         max_people_supported = available_units / units_per_person

#         if max_people_supported >= remaining_population:
#             remaining_population = 0
#         else:
#             remaining_population -= int(max_people_supported)

#     # ---------------- محاسبه محبوبیت ----------------
#     total = 0

#     # اثر گرسنگی
#     if remaining_population > 0:
#         if remaining_population <= 1000:
#             total -= 1
#         else:
#             total -= (remaining_population // 1000) + 1

#     # اثر ضریب مصرف
#     total += grain_consumption // 50  # هر ۵۰٪ مصرف = +۱ محبوبیت

#     return total

def calculate_hunger_and_consumption_popularity(province_name: str) -> int:
    """
    محاسبه تغییرات محبوبیت ناشی از گرسنگی و ضریب مصرف (نسخه جدید تک‌درصدی)
    grain_consumption: درصد کلی مصرف برای همه غلات
    """

    # پیدا کردن کشور و بارگذاری داده‌ها
    country_name = find_country_for_province(province_name)
    if not country_name:
        return 0

    province_data = load_province_data(country_name, province_name)
    if not province_data:
        return 0

    econ_path = os.path.join(ECONOMIC_FOLDER, province_name.replace(" ", "_") + ".json")
    econ_data = safe_load_json(econ_path)
    if not econ_data:
        return 0

    population = province_data.get("population", 0)
    items = province_data.get("economic_items", {}).copy()
    remaining_population = population

    # درصد کلی مصرف غلات
    grain_consumption = max(0, econ_data.get("grain_consumption", 0))

    # ---------------- بخش گرسنگی ----------------
    for grain, (base_people, base_units) in BASE_CONSUMPTION_RATES.items():
        # اگر موجودی این غله در استان نیست، رد کن
        food_amount = items.get(grain, 0)
        if food_amount <= 0:
            continue

        multiplier = 1 + (grain_consumption / 100)
        units_per_person = base_units / base_people * multiplier
        max_people_supported = food_amount / units_per_person

        if max_people_supported >= remaining_population:
            remaining_population = 0
            break
        else:
            remaining_population -= int(max_people_supported)

    # ---------------- محاسبه محبوبیت ----------------
    total = 0

    # اثر گرسنگی
    if remaining_population > 0:
        if remaining_population <= 1000:
            total -= 1
        else:
            total -= (remaining_population // 1000) + 1

    # اثر ضریب مصرف
    total += grain_consumption // 50  # هر ۵۰٪ مصرف = +۱ محبوبیت

    return total




async def toggle_block_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country = query.data.split(":")[1]

    file_path = "block_shop.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            blocked = json.load(f)
    else:
        blocked = []

    if country in blocked:
        blocked.remove(country)
    else:
        blocked.append(country)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(blocked, f, ensure_ascii=False, indent=2)

    await admin_lock_shop(update, context)



async def admin_lock_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کشورها برای قفل فروشگاه"""
    query = update.callback_query
    await query.answer()

    # خواندن لیست کشورها از فایل
    with open("countries.json", "r", encoding="utf-8") as f:
        countries_data = json.load(f)

    countries = list(countries_data["countries_areas"].keys())

    # خواندن لیست قفل‌شده‌ها
    if os.path.exists("block_shop.json"):
        with open("block_shop.json", "r", encoding="utf-8") as f:
            blocked = json.load(f)
    else:
        blocked = []

    text = "🛑 انتخاب کشورها برای قفل فروشگاه:\n\n"

    if blocked:
        text += "کشورهای قفل‌شده فعلی:\n" + "، ".join(blocked) + "\n\n"
    else:
        text += "هیچ کشوری قفل نشده است.\n\n"

    keyboard = []
    for country in countries:
        label = f"✅ {country}" if country in blocked else country
        keyboard.append([InlineKeyboardButton(label, callback_data=f"toggle_block_country:{country}")])

    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_manage_shop")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


def is_shop_blocked_for_user(user_province: str) -> bool:
    with open("countries.json", "r", encoding="utf-8") as f:
        countries_data = json.load(f)

    if not os.path.exists("block_shop.json"):
        return False

    with open("block_shop.json", "r", encoding="utf-8") as f:
        blocked_countries = json.load(f)

    for country, provinces in countries_data["countries_areas"].items():
        if user_province in provinces and country in blocked_countries:
            return True
    return False
