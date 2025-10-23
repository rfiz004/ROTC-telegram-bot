import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

# ======= 🔹 1. نمایش کشورها =======
async def show_country_list(update: Update, context: CallbackContext):
    countries = []
    base_path = os.path.join(os.getcwd(), "provinces")

    for file_name in os.listdir(base_path):
        if file_name.endswith(".json"):
            with open(os.path.join(base_path, file_name), "r", encoding="utf-8") as f:
                data = json.load(f)
            if "country" in data and data["country"] not in countries:
                countries.append(data["country"])

    keyboard = [
        [InlineKeyboardButton(country, callback_data=f"admin_select_country_{country}")]
        for country in countries
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_menu_back")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("🌍 یکی از کشورها را انتخاب کنید:", reply_markup=reply_markup)


# ======= 🔹 2. نمایش استان‌ها =======
async def show_provinces(update: Update, context: CallbackContext):
    country = update.callback_query.data.replace("admin_select_country_", "")
    base_path = os.path.join(os.getcwd(), "provinces")

    provinces = []
    for file_name in os.listdir(base_path):
        if file_name.endswith(".json"):
            with open(os.path.join(base_path, file_name), "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("country") == country:
                provinces.append(data["province"])

    keyboard = [
        [InlineKeyboardButton(prov, callback_data=f"admin_select_province_{prov}")]
        for prov in provinces
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_structure_status")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f"🏰 استان‌های کشور {country}:", reply_markup=reply_markup)


# ======= 🔹 3. نمایش آیتم‌های در انتظار =======
async def show_pending_items(update: Update, context: CallbackContext):
    province = update.callback_query.data.replace("admin_select_province_", "")
    base_path = os.path.join(os.getcwd(), "provinces")

    file_path = None
    for file_name in os.listdir(base_path):
        if province.lower() in file_name.lower():
            file_path = os.path.join(base_path, file_name)
            break

    if not file_path:
        await update.callback_query.edit_message_text("❌ فایل استان پیدا نشد.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pending_items = []
    for section, items in data.items():
        if isinstance(items, dict):
            for name, value in items.items():
                if isinstance(value, dict) and value.get("status", "").lower() == "pending":
                    pending_items.append((section, name))
    
    if not pending_items:
        await update.callback_query.edit_message_text("✅ هیچ سازه‌ی در انتظار تأییدی وجود ندارد.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{name} ({section})", callback_data=f"admin_review_item_{province}_{section}_{name}")]
        for section, name in pending_items
    ]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_structure_status")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f"🔎 سازه‌های در انتظار تأیید ({province}):", reply_markup=reply_markup)


# ======= 🔹 4. مرور آیتم =======
async def review_item(update: Update, context: CallbackContext):
    _, _, province, section, name = update.callback_query.data.split("_", 4)

    keyboard = [
        [
            InlineKeyboardButton("✅ تأیید", callback_data=f"admin_approve_item_{province}_{section}_{name}"),
            InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_item_{province}_{section}_{name}")
        ],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_select_province_{province}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        f"آیتم انتخاب‌شده:\n🏰 {name}\n📂 بخش: {section}\n\nمی‌خواهید تأیید یا رد شود؟",
        reply_markup=reply_markup
    )


# ======= 🔹 5. تابع آپدیت وضعیت =======
def update_item_status(province_name: str, section: str, structure_name: str, new_status: str):
    base_path = os.path.join(os.getcwd(), "provinces")
    target_file = None

    for file_name in os.listdir(base_path):
        if province_name.lower() in file_name.lower():
            target_file = os.path.join(base_path, file_name)
            break

    if not target_file:
        print(f"❌ فایل استان '{province_name}' پیدا نشد.")
        return False

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if section in data and structure_name in data[section]:
        if isinstance(data[section][structure_name], dict):
            data[section][structure_name]["status"] = new_status
        else:
            data[section][structure_name] = new_status

        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True

    return False


# ======= 🔹 6. تابع کاهش سازه =======
def decrement_structure_count(province_name: str, structure_name: str):
    base_path = os.path.join(os.getcwd(), "provinces")
    target_file = None
    for file_name in os.listdir(base_path):
        if file_name.endswith(".json") and province_name.lower() in file_name.lower():
            target_file = os.path.join(base_path, file_name)
            break

    if not target_file:
        print(f"❌ فایل استان '{province_name}' پیدا نشد.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sections = ["economic_structures", "structures", "castle", "mines", "weapons", "misc"]
    for section in sections:
        if section in data:
            if section == "economic_structures":
                for key, value in data[section].items():
                    if key == structure_name and isinstance(value, dict) and "count" in value:
                        value["count"] = max(0, value["count"] - 1)
                        break
            else:
                if structure_name in data[section]:
                    data[section][structure_name] = max(0, data[section][structure_name] - 1)
                    break

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======= 🔹 7. تأیید / رد =======
async def approve_item(update: Update, context: CallbackContext):
    _, _, province, section, name = update.callback_query.data.split("_", 4)
    update_item_status(province, section, name, "Approved")
    await update.callback_query.answer("✅ آیتم تأیید شد.", show_alert=True)
    await show_pending_items(update, context)


async def reject_item(update: Update, context: CallbackContext):
    _, _, province, section, name = update.callback_query.data.split("_", 4)
    update_item_status(province, section, name, "Rejected")
    decrement_structure_count(province, name)
    await update.callback_query.answer("❌ آیتم رد شد و از شمارش کم شد.", show_alert=True)
    await show_pending_items(update, context)
