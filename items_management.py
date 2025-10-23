import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler

# فایل‌ها
COUNTRIES_FILE = os.path.join(os.getcwd(), "countries.json")
DATA_FILE = os.path.join(os.getcwd(), "countries_data.json")
PROVINCES_DIR = os.path.join(os.getcwd(), "provinces")


# ===================== 1️⃣ نمایش کشورها =====================
async def show_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = list(data.get("countries_areas", {}).keys())

    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"admin_select_country_{country}")]
        for country in countries
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("🌍 یکی از کشورها را انتخاب کنید:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("🌍 یکی از کشورها را انتخاب کنید:", reply_markup=reply_markup)


# ===================== 2️⃣ نمایش استان‌ها =====================
async def show_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.callback_query.data.replace("admin_select_country_", "")

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    provinces = data.get("countries_areas", {}).get(country, [])

    keyboard = [
    [InlineKeyboardButton(prov, callback_data=f"admin_select_province_{country}_{prov}")]
    for prov in provinces
]

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f"🏰 استان‌های کشور {country}:", reply_markup=reply_markup)


# ===================== 3️⃣ نمایش آیتم‌های Pending =====================
async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_data = update.callback_query.data  # مثلاً: admin_select_province_Aldemar_Karnholm
    parts = query_data.split("_")

    # تشخیص کشور و استان از داده‌ی callback
    if len(parts) >= 5:
        country = parts[3]
        province = parts[4]
    else:
        await update.callback_query.edit_message_text("❌ داده انتخاب ناقص است.")
        return

    if not os.path.exists(DATA_FILE):
        await update.callback_query.edit_message_text("❌ فایل countries_data.json پیدا نشد.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # مسیر: کشور → استان
    province_data = data.get(country, {}).get(province, {})
    if not province_data:
        await update.callback_query.edit_message_text("❌ اطلاعات استان پیدا نشد.")
        return

    pending_items = []
    # پیمایش تمام بخش‌ها (castle, structures, weapons, economic_structures)
    for section, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if item.get("status", "").lower() == "pending":
                            pending_items.append((section, name, item["id"]))

    if not pending_items:
        await update.callback_query.edit_message_text(f"✅ هیچ سازه‌ی در انتظار تأییدی در {province} وجود ندارد.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{name} ({section})", callback_data=f"admin_review_item_{country}_{province}_{section}_{item_id}")]
        for section, name, item_id in pending_items
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_country_{country}")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.edit_message_text(
        f"🔎 آیتم‌های در انتظار تأیید ({province}):", reply_markup=reply_markup
    )


# ===================== 4️⃣ بروزرسانی وضعیت آیتم =====================
def update_item_status(country: str, province: str, section: str, item_id: str, new_status: str):
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
    _, country, province, section, item_id = update.callback_query.data.split("_", 4)
    update_item_status(country, province, section, item_id, "Approved")
    await update.callback_query.answer("✅ آیتم تأیید شد.", show_alert=True)
    await show_pending_items(update, context)


async def reject_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, country, province, section, item_id = update.callback_query.data.split("_", 4)
    update_item_status(country, province, section, item_id, "Rejected")
    decrement_structure_count(country, province, item_id)
    await update.callback_query.answer("❌ آیتم رد شد و از شمارش کم شد.", show_alert=True)
    await show_pending_items(update, context)

