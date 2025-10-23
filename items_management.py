import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler

# فایل‌ها
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

    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"admin_select_country_{country}")]
        for country in countries
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🌍 یکی از کشورها را انتخاب کنید:"

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


# ===================== 2️⃣ نمایش استان‌ها =====================
async def show_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش استان‌های کشور انتخاب‌شده."""
    query_data = update.callback_query.data
    country = query_data.replace("admin_select_country_", "", 1)

    if not os.path.exists(COUNTRIES_FILE):
        await update.callback_query.edit_message_text("❌ فایل countries.json پیدا نشد.")
        return

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    provinces = data.get("countries_areas", {}).get(country, [])

    if not provinces:
        await update.callback_query.edit_message_text(f"❌ استان‌های کشور '{country}' پیدا نشد.")
        return

    keyboard = [
        [InlineKeyboardButton(prov, callback_data=f"admin_select_province_{country}_{prov}")]
        for prov in provinces
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(f"🏰 استان‌های کشور {country}:", reply_markup=reply_markup)


# ===================== 3️⃣ نمایش آیتم‌های Pending =====================
async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آیتم‌های در انتظار تأیید (Pending)."""
    query_data = update.callback_query.data  # مثال: admin_select_province_Aldemar_Port_Zephalia

    prefix = "admin_select_province_"
    if not query_data.startswith(prefix):
        await update.callback_query.edit_message_text("❌ فرمت داده انتخاب اشتباه است.")
        return

    payload = query_data[len(prefix):]
    if "_" not in payload:
        await update.callback_query.edit_message_text("❌ داده انتخاب ناقص است.")
        return

    country, province = payload.split("_", 1)

    if not os.path.exists(DATA_FILE):
        await update.callback_query.edit_message_text("❌ فایل countries_data.json پیدا نشد.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    province_data = data.get(country, {}).get(province, {})
    if not province_data:
        await update.callback_query.edit_message_text(f"❌ اطلاعات استان '{province}' در '{country}' پیدا نشد.")
        return

    pending_items = []
    for section, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if item.get("status", "").lower() == "pending":
                            pending_items.append((section, name, item["id"]))

    if not pending_items:
        await update.callback_query.edit_message_text(f"✅ هیچ آیتم در انتظار تأییدی در {province} وجود ندارد.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{name} ({section})",
                              callback_data=f"admin_review_item_{country}_{province}_{section}_{item_id}")]
        for section, name, item_id in pending_items
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_country_{country}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"🔎 آیتم‌های در انتظار تأیید ({province}):", reply_markup=reply_markup
    )


# ===================== 7️⃣ نمایش جزئیات آیتم =====================
async def review_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جزئیات آیتم انتخاب‌شده برای تأیید یا رد."""
    query_data = update.callback_query.data
    prefix = "admin_review_item_"
    payload = query_data[len(prefix):]

    # بخش‌های داده را جدا می‌کنیم (country, province, section, item_id)
    parts = payload.split("_", 3)
    if len(parts) != 4:
        await update.callback_query.edit_message_text("❌ داده انتخاب اشتباه است.")
        return

    country, province, section, item_id = parts

    # داده‌ها را از فایل می‌خوانیم
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
        await update.callback_query.edit_message_text("❌ آیتم مورد نظر پیدا نشد.")
        return

    # متن نمایش داده‌شده
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
            InlineKeyboardButton("✅ تأیید", callback_data=f"admin_review_item_{country}_{province}_{section}_{item_id}_approve"),
            InlineKeyboardButton("❌ رد", callback_data=f"admin_review_item_{country}_{province}_{section}_{item_id}_reject"),
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_province_{country}_{province}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")



# ===================== 4️⃣ بروزرسانی وضعیت آیتم =====================
def update_item_status(country: str, province: str, section: str, item_id: str, new_status: str) -> bool:
    """بروزرسانی وضعیت آیتم به Approved یا Rejected."""
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


# ===================== 5️⃣ کاهش شمارش سازه (در صورت رد) =====================
def decrement_structure_count(country: str, province: str, item_id: str):
    """در صورت رد آیتم، شمارش سازه اقتصادی مرتبط را کاهش می‌دهد."""
    file_path = os.path.join(PROVINCES_DIR, f"{country}_{province}.json")
    if not os.path.exists(file_path):
        return

    with open(file_path, "r", encoding="utf-8") as f:
        province_data = json.load(f)

    for structure, info in province_data.get("economic_structures", {}).items():
        if info.get("count") and item_id.startswith(structure):
            info["count"] = max(0, info["count"] - 1)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(province_data, f, ensure_ascii=False, indent=2)


# ===================== 6️⃣ تأیید و رد آیتم =====================
async def approve_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید آیتم انتخاب‌شده."""
    query_data = update.callback_query.data
    prefix = "admin_review_item_"
    if not query_data.startswith(prefix):
        await update.callback_query.answer("❌ فرمت داده اشتباه است.", show_alert=True)
        return

    payload = query_data[len(prefix):]
    parts = payload.split("_", 3)
    if len(parts) != 4:
        await update.callback_query.answer("❌ داده ناقص است.", show_alert=True)
        return

    country, province, section, item_id = parts
    update_item_status(country, province, section, item_id, "Approved")
    await update.callback_query.answer("✅ آیتم تأیید شد.", show_alert=True)
    await show_pending_items(update, context)


async def reject_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد آیتم انتخاب‌شده."""
    query_data = update.callback_query.data
    prefix = "admin_review_item_"
    if not query_data.startswith(prefix):
        await update.callback_query.answer("❌ فرمت داده اشتباه است.", show_alert=True)
        return

    payload = query_data[len(prefix):]
    parts = payload.split("_", 3)
    if len(parts) != 4:
        await update.callback_query.answer("❌ داده ناقص است.", show_alert=True)
        return

    country, province, section, item_id = parts
    update_item_status(country, province, section, item_id, "Rejected")
    decrement_structure_count(country, province, item_id)
    await update.callback_query.answer("❌ آیتم رد شد و از شمارش کم شد.", show_alert=True)
    await show_pending_items(update, context)
