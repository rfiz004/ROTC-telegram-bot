# safe_admin_callbacks.py
import os
import json
import time
import uuid
from typing import Optional, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler

# فایل‌ها
BASE_DIR = os.getcwd()
COUNTRIES_FILE = os.path.join(BASE_DIR, "countries.json")
DATA_FILE = os.path.join(BASE_DIR, "countries_data.json")
PROVINCES_DIR = os.path.join(BASE_DIR, "provinces")

# ======== تنظیمات مدیریت payload mapping ========
# کلید در context.bot_data که نگهدارندهٔ mapping هست
CB_MAP_KEY = "cb_map"
# مدت زمان نگهداری payloadها (ثانیه) — این مقدار را لازم بود می‌توانی کم/زیاد کنی
CB_MAP_TTL = 60 * 60  # 1 hour


def _ensure_map(context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Dict[str, Any]]:
    """مطمئن شود cb_map وجود دارد و ورودی‌های قدیمی را پاک می‌کند."""
    bot_data = context.bot_data
    if CB_MAP_KEY not in bot_data:
        bot_data[CB_MAP_KEY] = {}
        return bot_data[CB_MAP_KEY]

    # پاکسازی ورودی‌های قدیمی
    now = time.time()
    to_del = []
    for uid, info in bot_data[CB_MAP_KEY].items():
        if now - info.get("_ts", 0) > CB_MAP_TTL:
            to_del.append(uid)
    for uid in to_del:
        del bot_data[CB_MAP_KEY][uid]

    return bot_data[CB_MAP_KEY]


def store_payload(context: ContextTypes.DEFAULT_TYPE, payload: Dict[str, Any]) -> str:
    """payload را ذخیره کن و یک uid کوتاه برگردان."""
    mapping = _ensure_map(context)
    uid = uuid.uuid4().hex[:16]  # 16 hex chars = 16 bytes (کوتاه و کافی)
    payload_copy = dict(payload)
    payload_copy["_ts"] = time.time()
    mapping[uid] = payload_copy
    return uid


def get_payload(context: ContextTypes.DEFAULT_TYPE, uid: str) -> Optional[Dict[str, Any]]:
    """payload را با uid برگردان (بدون فیلد _ts)."""
    mapping = _ensure_map(context)
    info = mapping.get(uid)
    if not info:
        return None
    payload = dict(info)
    payload.pop("_ts", None)
    return payload


# ===================== 1️⃣ نمایش کشورها =====================
async def show_country_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کشورها برای انتخاب."""
    # اگر از رسپانس callback است یا پیام جدید، هر دو را پشتیبانی می‌کنیم
    is_callback = bool(update.callback_query)

    if not os.path.exists(COUNTRIES_FILE):
        if is_callback:
            await update.callback_query.edit_message_text("❌ فایل countries.json پیدا نشد.")
        else:
            await update.message.reply_text("❌ فایل countries.json پیدا نشد.")
        return

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    countries = list(data.get("countries_areas", {}).keys())
    if not countries:
        if is_callback:
            await update.callback_query.edit_message_text("❌ هیچ کشوری یافت نشد.")
        else:
            await update.message.reply_text("❌ هیچ کشوری یافت نشد.")
        return

    keyboard = []
    for country in countries:
        uid = store_payload(context, {"action": "select_country", "country": country})
        # بجای "country_{uid}" از "country_select_{uid}" استفاده کن
        keyboard.append([InlineKeyboardButton(country, callback_data=f"country_select_{uid}")])


    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🌍 یکی از کشورها را انتخاب کنید:"

    if is_callback:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


# ===================== 2️⃣ نمایش استان‌های کشور =====================
async def show_provinces(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data  # e.g. "country_select_<uid>"

    if not data.startswith("country_select_"):
        await query.answer("❌ دادهٔ نا‌معتبر.", show_alert=True)
        return

    uid = data[len("country_select_"):]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "select_country":
        await query.answer("❌ دادهٔ انتخاب منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country = payload["country"]

    if not os.path.exists(COUNTRIES_FILE):
        await query.edit_message_text("❌ فایل countries.json پیدا نشد.")
        return

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
        data_file = json.load(f)

    provinces = data_file.get("countries_areas", {}).get(country, [])
    if not provinces:
        await query.edit_message_text(f"❌ هیچ استانی برای {country} پیدا نشد.")
        return

    keyboard = []
    for prov in provinces:
        sub_uid = store_payload(context, {"action": "select_province", "country": country, "province": prov})
        keyboard.append([InlineKeyboardButton(prov, callback_data=f"province_{sub_uid}")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"country_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"🏰 استان‌های کشور {country}:", reply_markup=reply_markup)


# ===================== 3️⃣ نمایش آیتم‌های Pending =====================
async def show_pending_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سازه‌های در انتظار تأیید."""
    query = update.callback_query
    data = query.data
    if not data.startswith("province_"):
        await query.answer("❌ دادهٔ نا‌معتبر.", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "select_province":
        await query.answer("❌ داده انتخاب منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country = payload["country"]
    province = payload["province"]

    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("❌ فایل countries_data.json پیدا نشد.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    province_data = all_data.get(country, {}).get(province, {})

    pending_items = []
    # پیمایش سازه‌ها
    for section, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if item.get("status", "").lower() == "pending":
                            pending_items.append({
                                "section": section,
                                "name": name,
                                "id": item.get("id")
                            })

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

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"province_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"🔎 آیتم‌های در انتظار تأیید ({province}):", reply_markup=reply_markup)


# ===================== 4️⃣ نمایش جزئیات آیتم =====================
async def review_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جزئیات آیتم برای تأیید یا رد."""
    query = update.callback_query
    data = query.data
    if not data.startswith("review_"):
        await query.answer("❌ دادهٔ نا‌معتبر.", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "review_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر است.", show_alert=True)
        return

    country = payload["country"]
    province = payload["province"]
    section = payload["section"]
    item_id = payload["item_id"]

    # خواندن دادهٔ آیتم از فایل
    if not os.path.exists(DATA_FILE):
        await query.edit_message_text("❌ فایل countries_data.json پیدا نشد.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    item_info = None
    province_data = data.get(country, {}).get(province, {})

    for section_name, items_dict in province_data.items():
        if isinstance(items_dict, dict):
            for name, items_list in items_dict.items():
                if isinstance(items_list, list):
                    for item in items_list:
                        if str(item.get("id")) == str(item_id):
                            item_info = item
                            break
                    if item_info:
                        break
            if item_info:
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

    # ساخت callbackهای کوتاه برای approve/reject با نگهداری payload
    appv_uid = store_payload(context, {
        "action": "approve_item",
        "country": country,
        "province": province,
        "section": section,
        "item_id": item_id
    })
    rej_uid = store_payload(context, {
        "action": "reject_item",
        "country": country,
        "province": province,
        "section": section,
        "item_id": item_id
    })

    keyboard = [
        [InlineKeyboardButton("✅ تأیید", callback_data=f"approve_{appv_uid}"),
         InlineKeyboardButton("❌ رد", callback_data=f"reject_{rej_uid}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"review_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")


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
                if isinstance(items_list, list):
                    for item in items_list:
                        if str(item.get("id")) == str(item_id):
                            item["status"] = new_status
                            updated = True

    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated


# ===================== 6️⃣ کاهش شمارش در صورت رد =====================
# def decrement_structure_count(country: str, province: str, item_id: str):
#     """در صورت رد آیتم، شمارش سازه را کاهش می‌دهد."""
#     file_path = os.path.join(PROVINCES_DIR, f"{country}_{province}.json")
#     if not os.path.exists(file_path):
#         return

#     with open(file_path, "r", encoding="utf-8") as f:
#         province_data = json.load(f)

#     for section_name in ["economic_structures", "structures", "castle"]:
#         section_data = province_data.get(section_name, {})
#         for structure, info in list(section_data.items()):
#             if isinstance(info, dict) and item_id.startswith(structure):
#                 info["count"] = max(0, info.get("count", 0) - 1)
#             elif isinstance(info, int) and item_id.startswith(structure):
#                 section_data[structure] = max(0, info - 1)

#     with open(file_path, "w", encoding="utf-8") as f:
#         json.dump(province_data, f, ensure_ascii=False, indent=2)
def decrement_structure_count(country: str, province: str, item_id: str):
    """
    در صورت رد آیتم، شمارش سازه را کاهش می‌دهد و منابع خرج‌شده را 
    با توجه به ساختار فایل استان (wealth و economic_items) بازمی‌گرداند.
    """
    file_path = os.path.join(PROVINCES_DIR, f"{country}_{province}.json")
    if not os.path.exists(file_path):
        print(f"⚠️ فایل استان {file_path} پیدا نشد.")
        return

    # 📖 خواندن داده‌ی استان
    with open(file_path, "r", encoding="utf-8") as f:
        province_data = json.load(f)

    structure_name = None

    # ۱️⃣ کم کردن شمارش سازه و پیدا کردن نامش
    for section_name in ["economic_structures", "structures", "castle"]:
        section_data = province_data.get(section_name, {})
        for structure, info in list(section_data.items()):
            if str(item_id).startswith(structure):
                structure_name = structure
                if isinstance(info, dict):
                    info["count"] = max(0, info.get("count", 0) - 1)
                elif isinstance(info, int):
                    section_data[structure] = max(0, info - 1)

    # ۲️⃣ بازگردانی منابع با توجه به shop_items.json
    shop_file = os.path.join(BASE_DIR, "shop_items.json")
    if not os.path.exists(shop_file):
        print("⚠️ فایل shop_items.json پیدا نشد، بازگردانی منابع انجام نشد.")
    else:
        with open(shop_file, "r", encoding="utf-8") as f:
            shop_items = json.load(f)

        # پیدا کردن آیتم با نام سازه
        item = next((i for i in shop_items if i.get("name") == structure_name), None)
        if item:
            refund_gold = item.get("price", 0)
            refund_materials = item.get("materials", {})

            # 💰 اضافه کردن طلا به wealth
            province_data["wealth"] = province_data.get("wealth", 0) + refund_gold

            # ⚙️ اضافه کردن مواد به economic_items
            if "economic_items" not in province_data:
                province_data["economic_items"] = {}

            for mat, val in refund_materials.items():
                province_data["economic_items"][mat] = province_data["economic_items"].get(mat, 0) + val

            print(f"💰 بازگردانی منابع انجام شد: {refund_gold} طلا و {len(refund_materials)} متریال برای '{structure_name}'")
        else:
            print(f"⚠️ آیتم '{structure_name}' در shop_items.json پیدا نشد.")

    # ۳️⃣ ذخیره تغییرات در فایل استان
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(province_data, f, ensure_ascii=False, indent=2)


# ===================== 7️⃣ تأیید و رد آیتم =====================
async def approve_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if not data.startswith("approve_"):
        await query.answer("❌ داده نامعتبر", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "approve_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر.", show_alert=True)
        return

    country = payload["country"]
    province = payload["province"]
    section = payload["section"]
    item_id = payload["item_id"]

    update_item_status(country, province, section, item_id, "Approved")
    await query.answer("✅ آیتم تأیید شد.", show_alert=True)

    # بعد از تأیید، بازگشت به لیست کشورها
    await show_country_list(update, context)


async def reject_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if not data.startswith("reject_"):
        await query.answer("❌ داده نامعتبر", show_alert=True)
        return

    uid = data.split("_", 1)[1]
    payload = get_payload(context, uid)
    if not payload or payload.get("action") != "reject_item":
        await query.answer("❌ داده منقضی شده یا نامعتبر.", show_alert=True)
        return

    country = payload["country"]
    province = payload["province"]
    section = payload["section"]
    item_id = payload["item_id"]

    update_item_status(country, province, section, item_id, "Rejected")
    decrement_structure_count(country, province, item_id)
    await query.answer("❌ آیتم رد شد.", show_alert=True)

    # بعد از رد، بازگشت به لیست کشورها
    await show_country_list(update, context)


# ===================== 8️⃣ هندلرهای برگشتی (back buttons) =====================
# اینها وقتی کاربر روی دکمهٔ بازگشت بزند رفتار را مشخص می‌کنند.
async def handle_back_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دکمه‌های بازگشت عمومی."""
    query = update.callback_query
    data = query.data

    if data == "country_back":
        # بازگشت به منوی کشورها
        await show_country_list(update, context)
        return
    if data == "province_back":
        # نمایش مجدد استان‌ها از payload قبلی اگر موجود باشد:
        # تلاش می‌کنیم payload آخر را پیدا کنیم که action == select_province و country match کند
        # اما ساده‌ترین رفتار بازگشت: بازگشت به countries list
        await show_country_list(update, context)
        return
    if data == "review_back":
        # بازگشت به منوی pending؛ بهترین کار بازگشت به لیست کشورها تا ساده و امن باشد
        await show_country_list(update, context)
        return

    # fallback
    await query.answer("❌ شناسهٔ بازگشت نامعتبر.", show_alert=True)
