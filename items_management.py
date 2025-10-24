import os
import json
import urllib.parse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


# مسیر فایل‌ها
BASE_DIR = os.getcwd()
COUNTRIES_FILE = os.path.join(BASE_DIR, "countries.json")
DATA_FILE = os.path.join(BASE_DIR, "countries_data.json")
PROVINCES_DIR = os.path.join(BASE_DIR, "provinces")


# ===================== 1️⃣ نمایش کشورها =====================
async def show_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کشورها برای انتخاب."""
    if not os.path.exists(COUNTRIES_FILE):
        await update.message.reply_text("❌ فایل countries.json پیدا نشد.")
        return

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = list(data.get("countries_areas", {}).keys())
    if not countries:
        await update.message.reply_text("❌ هیچ کشوری یافت نشد.")
        return

    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"admin_select_country_{urllib.parse.quote(country)}")]
        for country in countries
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🌍 یکی از کشورها را انتخاب کنید:"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


# ===================== 2️⃣ نمایش استان‌های کشور =====================
async def show_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش استان‌های کشور انتخاب‌شده."""
    query = update.callback_query
    country = urllib.parse.unquote(query.data.replace("admin_select_country_", "", 1))

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    provinces = data.get("countries_areas", {}).get(country, [])
    if not provinces:
        await query.edit_message_text(f"❌ هیچ استانی برای {country} پیدا نشد.")
        return

    keyboard = [
        [InlineKeyboardButton(prov, callback_data=f"admin_select_province_{urllib.parse.quote(country)}_{urllib.parse.quote(prov)}")]
        for prov in provinces
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])

    await query.edit_message_text(
        f"🏰 استان‌های کشور {country}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===================== 3️⃣ نمایش آیتم‌های Pending =====================
async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سازه‌های در انتظار تأیید."""
    query = update.callback_query
    data = query.data.replace("admin_select_province_", "", 1)
    try:
        country_enc, province_enc = data.split("_", 1)
        country = urllib.parse.unquote(country_enc)
        province = urllib.parse.unquote(province_enc)
    except ValueError:
        await query.edit_message_text("❌ داده انتخاب ناقص است.")
        return

    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("❌ فایل countries_data.json پیدا نشد.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    province_data = all_data.get(country, {}).get(province, {})
    pending_items = []

    for section, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                for item in items_list:
                    if item.get("status", "").lower() == "pending":
                        pending_items.append((section, name, item["id"]))

    if not pending_items:
        await query.edit_message_text(f"✅ هیچ آیتم در انتظار تأییدی در {province} وجود ندارد.")
        return

    keyboard = [
        [InlineKeyboardButton(
            f"{name} ({section})",
            callback_data=f"admin_review_item_{urllib.parse.quote(country)}_{urllib.parse.quote(province)}_{urllib.parse.quote(section)}_{urllib.parse.quote(item_id)}"
        )]
        for section, name, item_id in pending_items
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_country_{urllib.parse.quote(country)}")])

    await query.edit_message_text(
        f"🔎 آیتم‌های در انتظار تأیید ({province}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===================== 4️⃣ نمایش جزئیات آیتم =====================
async def review_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جزئیات آیتم برای تأیید یا رد."""
    query = update.callback_query
    payload = query.data.replace("admin_review_item_", "", 1)
    try:
        country_enc, province_enc, section_enc, item_id_enc = payload.split("_", 3)
    except ValueError:
        await query.edit_message_text("❌ داده انتخاب اشتباه است.")
        return

    country = urllib.parse.unquote(country_enc)
    province = urllib.parse.unquote(province_enc)
    section = urllib.parse.unquote(section_enc)
    item_id = urllib.parse.unquote(item_id_enc)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    item_info = None
    province_data = data.get(country, {}).get(province, {})

    for section_name, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                for item in items_list:
                    if item.get("id") == item_id:
                        item_info = item
                        break

    if not item_info:
        await query.edit_message_text("❌ آیتم پیدا نشد.")
        return

    text = (
        f"🗂 <b>بررسی آیتم</b>\n\n"
        f"🏴 کشور: {country}\n"
        f"🏰 استان: {province}\n"
        f"📦 بخش: {section}\n"
        f"🆔 شناسه: <code>{item_id}</code>\n"
        f"📋 جزئیات:\n"
    )
    for k, v in item_info.items():
        if k not in ["id", "status"]:
            text += f"   • {k}: {v}\n"

    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"admin_approve_item_{urllib.parse.quote(country)}_{urllib.parse.quote(province)}_{urllib.parse.quote(section)}_{urllib.parse.quote(item_id)}"),
            InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_item_{urllib.parse.quote(country)}_{urllib.parse.quote(province)}_{urllib.parse.quote(section)}_{urllib.parse.quote(item_id)}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_province_{urllib.parse.quote(country)}_{urllib.parse.quote(province)}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ===================== 5️⃣ بروزرسانی وضعیت آیتم =====================
def update_item_status(country: str, province: str, section: str, item_id: str, new_status: str) -> bool:
    """بروزرسانی وضعیت آیتم."""
    if not os.path.exists(DATA_FILE):
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    province_data = data.get(country, {}).get(province, {})
    updated = False

    for section_name, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                for item in items_list:
                    if item.get("id") == item_id:
                        item["status"] = new_status
                        updated = True

    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


# ===================== 6️⃣ کاهش شمارش در صورت رد =====================
def decrement_structure_count(country: str, province: str, item_id: str):
    """در صورت رد آیتم، شمارش سازه را کاهش می‌دهد."""
    file_path = os.path.join(PROVINCES_DIR, f"{country}_{province}.json")
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as f:
        province_data = json.load(f)

    for section_name in ["economic_structures", "structures", "castle"]:
        section_data = province_data.get(section_name, {})
        for structure, info in list(section_data.items()):
            if isinstance(info, dict) and item_id.startswith(structure):
                info["count"] = max(0, info.get("count", 0) - 1)
            elif isinstance(info, int) and item_id.startswith(structure):
                section_data[structure] = max(0, info - 1)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(province_data, f, ensure_ascii=False, indent=2)


# ===================== 7️⃣ تأیید و رد آیتم =====================
async def approve_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    payload = query.data.replace("admin_approve_item_", "", 1)
    country, province, section, item_id = [urllib.parse.unquote(p) for p in payload.split("_", 3)]

    update_item_status(country, province, section, item_id, "Approved")
    await query.answer("✅ آیتم تأیید شد.", show_alert=True)
    await show_country_list(update, context)


async def reject_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    payload = query.data.replace("admin_reject_item_", "", 1)
    country, province, section, item_id = [urllib.parse.unquote(p) for p in payload.split("_", 3)]

    update_item_status(country, province, section, item_id, "Rejected")
    decrement_structure_count(country, province, item_id)
    await query.answer("❌ آیتم رد شد.", show_alert=True)
    await show_country_list(update, context)
