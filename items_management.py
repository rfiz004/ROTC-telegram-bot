# safe_admin_callbacks.py (بازنویسی‌شده و رفع باگ‌ها)
# توضیح کوتاه: این نسخه باگ اصلیِ منطق callback payload (افزودن/پوشش `action`) را رفع می‌کند
# و چند بهبود جزئی در بررسی ورودی و خطایابی اضافه شده است.

import os
import json
import time
import uuid
from typing import Optional, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# فایل‌ها
BASE_DIR = os.getcwd()
COUNTRIES_FILE = os.path.join(BASE_DIR, "countries.json")
DATA_FILE = os.path.join(BASE_DIR, "countries_data.json")
PROVINCES_DIR = os.path.join(BASE_DIR, "provinces")

# ======== تنظیمات mapping ========
CB_MAP_KEY = "cb_map"
CB_MAP_TTL = 60 * 60  # 1 hour


def _ensure_map(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Dict[str, Any]]:
    bot_data = context.bot_data
    if CB_MAP_KEY not in bot_data:
        bot_data[CB_MAP_KEY] = {}
        return bot_data[CB_MAP_KEY]

    now = time.time()
    expired = [uid for uid, info in bot_data[CB_MAP_KEY].items() if now - info.get("_ts", 0) > CB_MAP_TTL]
    for uid in expired:
        del bot_data[CB_MAP_KEY][uid]
    return bot_data[CB_MAP_KEY]


def store_payload(context: ContextTypes.DEFAULT_TYPE, payload: Dict[str, Any]) -> str:
    mapping = _ensure_map(context)
    uid = uuid.uuid4().hex[:16]
    payload_copy = dict(payload)
    payload_copy["_ts"] = time.time()
    mapping[uid] = payload_copy
    return uid


def get_payload(context: ContextTypes.DEFAULT_TYPE, uid: str) -> Optional[Dict[str, Any]]:
    mapping = _ensure_map(context)
    info = mapping.get(uid)
    if not info:
        return None
    payload = dict(info)
    payload.pop("_ts", None)
    return payload


# ===================== 1️⃣ لیست کشورها =====================
async def show_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_callback = bool(getattr(update, "callback_query", None))

    if not os.path.exists(COUNTRIES_FILE):
        msg = "❌ فایل countries.json پیدا نشد."
        if is_callback:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    try:
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        msg = f"❌ خطا در خواندن countries.json: {e}"
        if is_callback:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    countries = list(data.get("countries_areas", {}).keys())
    if not countries:
        msg = "❌ هیچ کشوری یافت نشد."
        if is_callback:
            await update.callback_query.edit_message_text(msg)
        else:
            await update.message.reply_text(msg)
        return

    keyboard = []
    for country in countries:
        uid = store_payload(context, {"action": "select_country", "country": country})
        keyboard.append([InlineKeyboardButton(country, callback_data=f"country_select_{uid}")])

    sender = update.callback_query.edit_message_text if is_callback else update.message.reply_text
    await sender("🌍 یکی از کشورها را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


# ===================== 2️⃣ استان‌های کشور =====================
async def show_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = getattr(query, "data", "")

    if not data.startswith("country_select_"):
        await query.answer("❌ دادهٔ نامعتبر.", show_alert=True)
        return

    uid = data.replace("country_select_", "", 1)
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "select_country":
        await query.answer("❌ دادهٔ انتخاب منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country = payload["country"]

    try:
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except Exception as e:
        await query.edit_message_text(f"❌ خطا در خواندن countries.json: {e}")
        return

    provinces = all_data.get("countries_areas", {}).get(country, [])
    if not provinces:
        await query.edit_message_text(f"❌ هیچ استانی برای {country} پیدا نشد.")
        return

    keyboard = []
    for prov in provinces:
        sub_uid = store_payload(context, {"action": "select_province", "country": country, "province": prov})
        keyboard.append([InlineKeyboardButton(prov, callback_data=f"province_{sub_uid}")])

    # دکمه بازگشت با payload کشور
    back_uid = store_payload(context, {"action": "back_to_countries"})
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_{back_uid}")])

    await query.edit_message_text(f"🏰 استان‌های کشور {country}:", reply_markup=InlineKeyboardMarkup(keyboard))


# ===================== 3️⃣ آیتم‌های Pending =====================
async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = getattr(query, "data", "")

    if not data.startswith("province_"):
        await query.answer("❌ دادهٔ نامعتبر.", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "select_province":
        await query.answer("❌ داده انتخاب منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country = payload["country"]
    province = payload["province"]

    if not os.path.exists(DATA_FILE):
        await query.edit_message_text(f"❌ فایل داده‌ها ({DATA_FILE}) پیدا نشد.")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except Exception as e:
        await query.edit_message_text(f"❌ خطا در خواندن داده‌ها: {e}")
        return

    province_data = all_data.get(country, {}).get(province, {})
    pending_items = []
    for section, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if item.get("status", "").lower() == "pending":
                            pending_items.append({"section": section, "name": name, "id": item.get("id")})

    if not pending_items:
        await query.edit_message_text(f"✅ هیچ آیتم در انتظار تأییدی در {province} وجود ندارد.")
        return

    keyboard = []
    for itm in pending_items:
        rev_uid = store_payload(context, {
            "action": "review_item",
            "country": country,
            "province": province,
            "section": itm["section"],
            "name": itm["name"],
            "item_id": itm["id"]
        })
        keyboard.append([InlineKeyboardButton(f"{itm['name']} ({itm['section']})", callback_data=f"review_{rev_uid}")])

    # 🔙 دکمه بازگشت با payload استان
    back_uid = store_payload(context, {"action": "back_to_provinces", "country": country, "province": province})
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_{back_uid}")])

    await query.edit_message_text(f"🔎 آیتم‌های در انتظار تأیید ({province}):", reply_markup=InlineKeyboardMarkup(keyboard))


# ===================== 4️⃣ جزئیات آیتم =====================
async def review_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = getattr(query, "data", "")
    if not data.startswith("review_"):
        await query.answer("❌ دادهٔ نامعتبر.", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "review_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country, province, section, item_id = payload["country"], payload["province"], payload["section"], payload["item_id"]

    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("❌ فایل داده‌ها پیدا نشد.")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data_file = json.load(f)
    except Exception as e:
        await query.edit_message_text(f"❌ خطا در خواندن داده‌ها: {e}")
        return

    province_data = data_file.get(country, {}).get(province, {})
    item_info = None
    for sect, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if str(item.get("id")) == str(item_id):
                            item_info = item
                            break

    if not item_info:
        await query.edit_message_text("❌ آیتم پیدا نشد.")
        return

    text = f"🗂 <b>بررسی آیتم</b>\n\n🏴 کشور: {country}\n🏰 استان: {province}\n📦 بخش: {section}\n🆔 <code>{item_id}</code>\n\n📋 جزئیات:\n"
    for k, v in item_info.items():
        if k not in ["id", "status"]:
            text += f"• {k}: {v}\n"

    # **⚠️ مهم: ترتیب ادغام دیکشنری‌ها برای تعیین `action` صحیح مهم است.**
    # payload ممکن است شامل action="review_item" باشد؛ بنابراین ابتدا محتویات payload
    # را قرار می‌دهیم و سپس action جدید را می‌گذاریم تا مقدار قبلی بازنویسی شود.
    appv_uid = store_payload(context, {**payload, "action": "approve_item"})
    rej_uid = store_payload(context, {**payload, "action": "reject_item"})
    back_uid = store_payload(context, {"action": "back_to_pending", "country": country, "province": province})

    keyboard = [
        [InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{appv_uid}"),
         InlineKeyboardButton("❌ رد", callback_data=f"reject_{rej_uid}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_{back_uid}")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ===================== 5️⃣ آپدیت وضعیت آیتم =====================
def update_item_status(country: str, province: str, section: str, item_id: str, new_status: str) -> bool:
    if not os.path.exists(DATA_FILE):
        return False
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False

    province_data = data.get(country, {}).get(province, {})
    updated = False
    for sect, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if str(item.get("id")) == str(item_id):
                            item["status"] = new_status
                            updated = True
    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return updated


# ===================== 6️⃣ کاهش شمارش و بازگردانی منابع =====================
def decrement_structure_count(country: str, province: str, item_id: str):
    file_path = os.path.join(PROVINCES_DIR, f"{country}_{province}.json")
    if not os.path.exists(file_path):
        print(f"⚠️ فایل {file_path} پیدا نشد.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            province_data = json.load(f)
    except Exception as e:
        print(f"⚠️ خطا در خواندن {file_path}: {e}")
        return

    structure_name = None
    for section_name in ["economic_structures", "structures", "castle"]:
        section_data = province_data.get(section_name, {})
        if isinstance(section_data, dict):
            for structure, info in list(section_data.items()):
                # اگر item_id با نام سازه شروع بشه → فرض می‌کنیم این آیتم متعلق به آن سازه است
                if str(item_id).startswith(str(structure)):
                    structure_name = structure
                    if isinstance(info, dict):
                        info["count"] = max(0, info.get("count", 0) - 1)
                    elif isinstance(info, int):
                        section_data[structure] = max(0, info - 1)

    shop_file = os.path.join(BASE_DIR, "shop_items.json")
    if os.path.exists(shop_file):
        try:
            with open(shop_file, "r", encoding="utf-8") as f:
                shop_items = json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن shop_items.json: {e}")
            shop_items = []

        item = next((i for i in shop_items if i.get("name") == structure_name), None)
        if item:
            refund_gold = item.get("price", 0)
            refund_materials = item.get("materials", {})
            province_data["wealth"] = province_data.get("wealth", 0) + refund_gold
            econ = province_data.setdefault("economic_items", {})
            for mat, val in refund_materials.items():
                econ[mat] = econ.get(mat, 0) + val
            print(f"💰 بازگردانی منابع: {refund_gold} طلا و {len(refund_materials)} متریال برای {structure_name}")
        else:
            print(f"⚠️ آیتم '{structure_name}' یافت نشد.")
    else:
        print("⚠️ shop_items.json یافت نشد.")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(province_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در نوشتن {file_path}: {e}")


# ===================== 7️⃣ تأیید / رد =====================
async def approve_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "approve_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر.", show_alert=True)
        return

    ok = update_item_status(payload["country"], payload["province"], payload["section"], payload["item_id"], "Approved")
    if not ok:
        await query.answer("❌ بروزرسانی وضعیت با خطا مواجه شد.", show_alert=True)
        return

    await query.answer("✅ آیتم تأیید شد.", show_alert=True)
    # بازگشت به لیست کشورها (یا می‌توان مستقیما لیست استان‌ها را نشان داد)
    await show_country_list(update, context)


async def reject_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "reject_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر.", show_alert=True)
        return

    ok = update_item_status(payload["country"], payload["province"], payload["section"], payload["item_id"], "Rejected")
    if not ok:
        await query.answer("❌ بروزرسانی وضعیت با خطا مواجه شد.", show_alert=True)
        return

    decrement_structure_count(payload["country"], payload["province"], payload["item_id"])
    await query.answer("❌ آیتم رد شد.", show_alert=True)
    await show_country_list(update, context)


# ===================== 8️⃣ دکمه‌های بازگشت =====================
async def handle_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = getattr(query, "data", "")

    if not data.startswith("back_"):
        await query.answer("❌ دادهٔ بازگشت نامعتبر.", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)

    # اگر payload از بین رفته باشه → برگرد به لیست کشورها
    if not payload:
        await show_country_list(update, context)
        return

    action = payload.get("action")
    country = payload.get("country")
    province = payload.get("province")

    # 🔹 مرحله ۱: بازگشت از صفحه استان‌ها به کشورها
    if action == "back_to_countries":
        await show_country_list(update, context)
        return

    # 🔹 مرحله ۲: بازگشت از Pending‌ها به استان‌های کشور
    elif action == "back_to_provinces":
        if not country:
            await show_country_list(update, context)
            return
        fake_uid = store_payload(context, {"action": "select_country", "country": country})
        # بازنویسی داده callback و فراخوانی مستقیم تابع استان‌ها
        update.callback_query.data = f"country_select_{fake_uid}"
        await show_provinces(update, context)
        return

    # 🔹 مرحله ۳: بازگشت از صفحه بررسی آیتم‌ها به لیست Pending
    elif action == "back_to_pending":
        if not (country and province):
            await show_country_list(update, context)
            return
        fake_uid = store_payload(context, {"action": "select_province", "country": country, "province": province})
        update.callback_query.data = f"province_{fake_uid}"
        await show_pending_items(update, context)
        return

    # 🔹 حالت پیش‌فرض: برگرد به صفحه کشورها
    else:
        await show_country_list(update, context)
