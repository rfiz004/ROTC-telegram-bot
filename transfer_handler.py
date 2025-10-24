
"""
Transfer handler module - handles character transfers between provinces/countries
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import back_and_home_buttons
import json
import os
import uuid
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from province_handler import load_province_data, save_province_data

logger = logging.getLogger(__name__)

TRANSFERS_FILE = "data/transfers.json"

async def handle_transfer_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submit a transfer request"""

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    category = user_data.get("transfer_category")
    items_raw = user_data.get("transfer_items_input", "")
    source_country = user_data.get("country")
    source_province = user_data.get("province")
    target_country = user_data.get("transfer_target_country")
    target_province = user_data.get("transfer_target_province")
    transfer_type = user_data.get("transfer_type")

    if not all([category, items_raw, source_country, source_province, target_country, target_province]):
        await update.message.reply_text("❌ اطلاعات انتقال ناقص است.")
        return

    # پردازش اقلام
    items = {}
    lines = items_raw.strip().split("\n")
    for line in lines:
        if ":" in line:
            name, qty = line.split(":", 1)
            try:
                quantity = int(qty.strip())
                items[name.strip()] = quantity
            except:
                continue

    if not items:
        await update.message.reply_text("❌ فرمت اقلام نامعتبر است.")
        return

    transfer_entry = {
        "id": uuid.uuid4().hex,
        "requester_id": user_id,
        "source_country": source_country,
        "source_province": source_province,
        "target_country": target_country,
        "target_province": target_province,
        "transfer_type": transfer_type,
        "category": category,
        "items": items,
        "status": "pending",
        "requested_at": datetime.utcnow().isoformat()
    }

    transfers_data = load_pending_transfers()
    transfers_data.setdefault("transfers", []).append(transfer_entry)
    save_pending_transfers(transfers_data)

    # حذف state از context
    context.user_data[user_id].pop("step", None)
    context.user_data[user_id].pop("transfer_items_input", None)

    await update.message.reply_text("✅ درخواست انتقال ثبت شد و در انتظار تأیید است.")

async def approve_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    transfer_id = query.data.replace("approve_transfer_", "")
    transfers_data = load_pending_transfers()

    for transfer in transfers_data.get("transfers", []):
        if transfer.get("id") == transfer_id and transfer.get("status") == "pending":
            transfer["status"] = "approved"
            transfer["approved_at"] = datetime.utcnow().isoformat()
            break
    else:
        await query.edit_message_text("❌ انتقال پیدا نشد یا قبلاً تأیید شده.")
        return

    save_pending_transfers(transfers_data)
    await query.edit_message_text("✅ انتقال تأیید شد.")

async def reject_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reject transfer request"""
    # Placeholder implementation
    query = update.callback_query
    await query.answer()

    transfer_id = query.data.replace("reject_transfer_", "")
    transfers_data = load_pending_transfers()

    for transfer in transfers_data.get("transfers", []):
        if transfer.get("id") == transfer_id and transfer.get("status") == "pending":
            transfer["status"] = "rejected"
            transfer["rejected_at"] = datetime.utcnow().isoformat()
            break
    else:
        await query.edit_message_text("❌ انتقال پیدا نشد یا قبلاً رد شده.")
        return

    save_pending_transfers(transfers_data)
    await query.edit_message_text("🚫 انتقال رد شد.")

def load_pending_transfers():
    """Load pending transfers from file"""
    if not os.path.exists(TRANSFERS_FILE):
        os.makedirs("data", exist_ok=True)
        default_data = {"transfers": []}
        with open(TRANSFERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

    try:
        with open(TRANSFERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading transfers: {e}")
        return {"transfers": []}

def save_pending_transfers(transfers_data):
    """Save pending transfers to file"""
    try:
        os.makedirs("data", exist_ok=True)
        with open(TRANSFERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(transfers_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving transfers: {e}")
        return False

# def save_pending_transfers(data):
#     """Save pending transfers to file"""
#     os.makedirs("data", exist_ok=True)
#     with open(TRANSFERS_FILE, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

# async def view_pending_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
#         """View pending transfers for the user"""
#         query = update.callback_query
#         await query.answer()

#         try:
#             transfers_data = load_pending_transfers()
#             user_transfers = [t for t in transfers_data.get("transfers", []) if t.get("status") == "pending"]

#             if not user_transfers:
#                     text = "📭 هیچ انتقال در انتظاری یافت نشد."
#             else:
#                 text = "🔄 انتقالات در انتظار:\n\n"
#                 for i, transfer in enumerate(user_transfers, 1):
#                     text += f"{i}. {transfer.get('source_country', 'نامشخص')}-{transfer.get('source_province', 'نامشخص')} → "
#                     text += f"{transfer.get('target_country', 'نامشخص')}-{transfer.get('target_province', 'نامشخص')}\n"

#                     items = transfer.get("items", {})
#                     if items:
#                         for name, qty in items.items():
#                                 text += f"   📦 {name} × {qty:,}\n"
#                     else:
#                         text += "   📦 نامشخص × 0\n"

#                     text += f"   🔄 نوع: {transfer.get('transfer_type', 'نامشخص')}\n\n"

#             keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")]]
#             await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

#         except Exception as e:
#             logger.error(f"Error viewing pending transfers: {e}")
#             await query.edit_message_text("❌ خطا در نمایش انتقالات در انتظار")


async def show_transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transfer system menu"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    # Import check_admin_access function
    from utils import check_admin_access

    # Allow province admins, country admins, and master admins
    has_access = (
        check_admin_access(user_data, required_role="master_admin") or
        check_admin_access(user_data, required_role="multi_admin_1") or
        check_admin_access(user_data, required_role="multi_admin_2") or
        check_admin_access(user_data, required_role="multi_admin_3") or
        user_data.get("country")  # Province admins who have country access
    )

    if not has_access:
        await query.edit_message_text(
            "❌ دسترسی غیرمجاز. انتقالات فقط برای ادمین‌های مجاز و مدیران استان است.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_previous")
            ]])
        )
        return

    # Show note about approval process for non-master admins
    note_text = ""
    if not check_admin_access(user_data, required_role="master_admin"):
        note_text = "\n\n⚠️ توجه: انتقالات شما نیاز به تایید مدیر کل دارد."

    buttons = [
        [InlineKeyboardButton("🏠 انتقال داخلی", callback_data="transfer_domestic")],
        [InlineKeyboardButton("🌍 انتقال بین‌المللی", callback_data="transfer_international")],
        [InlineKeyboardButton("📋 انتقالات در انتظار", callback_data="view_pending_transfers")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")]
    ]

    await query.edit_message_text(
        f"📦 سیستم انتقالات\nنوع انتقال را انتخاب کنید:{note_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )



async def show_domestic_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show domestic transfer options"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    country = user_data.get("country")
    current_province = user_data.get("province")

    # Push navigation state
    from callback_handlers import push_navigation_state
    push_navigation_state(user_data, "transfer_menu")

    # Get all provinces from countries.json
    try:
        with open("countries.json", 'r', encoding='utf-8') as f:
            countries_data = json.load(f)
        
        all_provinces = countries_data.get("countries_areas", {}).get(country, [])
        # Remove current province from options
        same_country_provinces = [p for p in all_provinces if p != current_province]
        
    except Exception as e:
        logging.error(f"Error loading provinces: {e}")
        same_country_provinces = []

    if not same_country_provinces:
        text = "هیچ استان دیگری در کشور شما موجود نیست."
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text = f"🏠 انتقال داخلی در {country}\n\nاستان مقصد را انتخاب کنید:"

    keyboard = []
    for province in same_country_provinces:
        # Use safe province name for callback data
        safe_province = province.replace(" ", "_").replace("'", "")
        keyboard.append([InlineKeyboardButton(
            province, 
            callback_data=f"domestic_target_{safe_province}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")])

    context.user_data[user_id]["step"] = "awaiting_transfer_items_input"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["state"] = None  # یا مقدار مناسب دیگه اگر نیاز هست

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_international_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show international transfer options (any province to capital only)"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})
    current_country = user_data.get("country")

    # Push navigation state
    from callback_handlers import push_navigation_state
    push_navigation_state(user_data, "transfer_menu")

    # Import capital cities configuration
    from config import CAPITAL_CITIES

    # Get all other countries (exclude current country)
    available_countries = [country for country in CAPITAL_CITIES.keys() if country != current_country]

    if not available_countries:
        text = "هیچ کشور دیگری برای انتقال بین‌المللی موجود نیست."
        keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text = "🌍 انتقال بین‌المللی\n\nکشور مقصد را انتخاب کنید:\n\n"
    text += "⚠️ انتقال بین‌المللی فقط به پایتخت کشورها امکان‌پذیر است."

    keyboard = []
    for country in available_countries:
        capital = CAPITAL_CITIES.get(country, "پایتخت")
        keyboard.append([InlineKeyboardButton(
            f"{country} ({capital})", 
            callback_data=f"international_target_{country}_{capital}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")])

    context.user_data[user_id]["step"] = "awaiting_transfer_items_input"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["state"] = None  # یا مقدار مناسب دیگه اگر نیاز هست

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_transfer_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show items available for transfer"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Extract target from callback data
    if query.data.startswith("domestic_target_"):
        target_province = query.data.replace("domestic_target_", "").replace("_", " ")
        target_country = user_data.get("country", "نامشخص")
        transfer_type = "domestic"
    elif query.data.startswith("international_target_"):
        target_data = query.data.replace("international_target_", "")
        parts = target_data.split("_")
        if len(parts) >= 2:
            target_country = parts[0]
            target_province = "_".join(parts[1:]).replace("_", " ")
        else:
            await query.edit_message_text("خطا در تشخیص مقصد بین‌المللی.")
            return
        transfer_type = "international"
    else:
        await query.edit_message_text("خطا در تشخیص مقصد.")
        return

    # Store transfer info
    context.user_data[user_id]["transfer_target_country"] = target_country
    context.user_data[user_id]["transfer_target_province"] = target_province
    context.user_data[user_id]["transfer_type"] = transfer_type

    context.user_data[user_id]["step"] = "awaiting_transfer_category"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["state"] = None

    # Get current province data
    country = user_data["country"]
    province = user_data["province"]
    province_data = load_province_data(country, province)

    text = f"📦 انتقال به {target_country} - {target_province}\n\n"
    text += "دسته‌بندی آیتم مورد نظر را انتخاب کنید:\n\n"

    keyboard = []

    # Always show all transfer categories, even if empty (user might want to see what's available)
    
    # Economic Items
    keyboard.append([InlineKeyboardButton("🌾 اقلام اقتصادی", callback_data="transfer_category_economic_items")])

    # Miscellaneous
    keyboard.append([InlineKeyboardButton("📦 متفرقه", callback_data="transfer_category_misc")])

    # Army units (Soldiers)
    keyboard.append([InlineKeyboardButton("⚔️ سربازان", callback_data="transfer_category_army")])

    # Structures
    keyboard.append([InlineKeyboardButton("🏗️ سازه‌ها", callback_data="transfer_category_structures")])

    # Weapons
    keyboard.append([InlineKeyboardButton("🗡️ سلاح‌ها", callback_data="transfer_category_weapons")])

    # Money/Wealth
    keyboard.append([InlineKeyboardButton("💰 پول", callback_data="transfer_category_wealth")])

    # Population (only for domestic transfers)
    if transfer_type == "domestic":
        keyboard.append([InlineKeyboardButton("👥 جمعیت", callback_data="transfer_category_population")])

    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_transfer_category_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category and prompt for text input"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    category = query.data.replace("transfer_category_", "")

    country = user_data["country"]
    province = user_data["province"]
    province_data = load_province_data(country, province)

    target_country = user_data["transfer_target_country"]
    target_province = user_data["transfer_target_province"]
    transfer_type = user_data["transfer_type"]

    # Store category for later use
    context.user_data[user_id]["transfer_category"] = category
    context.user_data[user_id]["step"] = "awaiting_transfer_items_input"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["state"] = None

    text = f"📦 انتقال {category} به {target_country} - {target_province}\n\n"

    if category == "economic_items":
        text += "اقلام اقتصادی موجود:\n"
        for item, count in province_data.get("economic_items", {}).items():
            if count > 0:
                text += f"• {item}: {count:,}\n"
        text += "\n💡 آیتم‌ها و مقادیر را به فرمت زیر وارد کنید:\nگندم: 100\nگوشت: 50\nفولاد: 25"

    # elif category == "misc":
    #     text += "آیتم‌های متفرقه موجود:\n"
    #     misc_items = province_data.get("misc", [])
    #     for i, item in enumerate(misc_items, 1):
    #         text += f"{i}. {item}\n"
    #     text += "\n💡 آیتم‌ها را به فرمت زیر وارد کنید:\nنام آیتم 1: 1\nنام آیتم 2: 1"

    # elif category == "weapons":
    #     text += "سلاح‌های موجود:\n"
    #     weapons = province_data.get("weapons", [])
    #     for i, weapon in enumerate(weapons, 1):
    #         text += f"{i}. {weapon}\n"
    #     text += "\n💡 سلاح‌ها را به فرمت زیر وارد کنید:\nنام سلاح 1: 1\nنام سلاح 2: 1"

    # elif category == "structures":
    #     text += "سازه‌های موجود:\n"
    #     structures = province_data.get("structures", [])
    #     for i, structure in enumerate(structures, 1):
    #         text += f"{i}. {structure}\n"
    #     text += "\n💡 سازه‌ها را به فرمت زیر وارد کنید:\nنام سازه 1: 1\nنام سازه 2: 1"

    elif category == "misc":
        text += "آیتم‌های متفرقه موجود:\n"
        for item, count in province_data.get("misc", {}).items():
            if count > 0:
                text += f"• {item}: {count:,}\n"
        text += "\n💡 آیتم‌ها را به فرمت زیر وارد کنید:\nنام آیتم 1: 1\nنام آیتم 2: 1"
    
    elif category == "weapons":
        text += "سلاح‌های موجود:\n"
        for weapon, count in province_data.get("weapons", {}).items():
            if count > 0:
                text += f"• {weapon}: {count:,}\n"
        text += "\n💡 سلاح‌ها را به فرمت زیر وارد کنید:\nنام سلاح 1: 1\nنام سلاح 2: 1"
    
    elif category == "structures":
        text += "سازه‌های موجود:\n"
        for structure, count in province_data.get("structures", {}).items():
            if count > 0:
                text += f"• {structure}: {count:,}\n"
        text += "\n💡 سازه‌ها را به فرمت زیر وارد کنید:\nنام سازه 1: 1\nنام سازه 2: 1"

    elif category == "army":
        text += "نیروهای نظامی موجود:\n"
        for unit, count in province_data.get("army", {}).items():
            if count > 0:
                text += f"• {unit}: {count:,}\n"
        text += "\n💡 نیروها و تعداد را به فرمت زیر وارد کنید:\nکماندار: 100\nشمشیرزن: 50"

    elif category == "wealth":
        current_wealth = province_data.get("wealth", 0)
        text += f"ثروت موجود: {current_wealth:,} طلا\n\n"
        text += "💡 مقدار طلا را وارد کنید:\n500"

    elif category == "population":
        current_pop = province_data.get("population", 0)
        max_transferable = current_pop // 2  # Max 50% of population
        text += f"جمعیت موجود: {current_pop:,} نفر\n"
        text += f"حداکثر قابل انتقال: {max_transferable:,} نفر\n\n"
        text += "💡 تعداد جمعیت را وارد کنید:\n1000"

    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="transfer_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_transfer_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity input for transfer"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Parse transfer item data
    transfer_data = query.data.replace("transfer_item_", "")
    category, item_name = transfer_data.split("_", 1)

    context.user_data[user_id]["transfer_category"] = category
    context.user_data[user_id]["transfer_item"] = item_name
    context.user_data[user_id]["step"] = "awaiting_transfer_quantity"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["state"] = None

    # Get current amount
    country = user_data["country"]
    province = user_data["province"]
    province_data = load_province_data(country, province)

    # if category == "army":
    #     current_amount = province_data["army"].get(item_name, 0)
    # elif category == "weapons":
    #     current_amount = province_data["weapons"].get(item_name, 0)
    # elif category == "goods":
    #     current_amount = province_data["economic_goods"].get(item_name, 0)
    # elif category == "money":
    #     current_amount = province_data["wealth"]
    # elif category == "population":
    #     current_amount = province_data["population"] // 2  # Max 50%
    # else:
    #     current_amount = 0


    if category == "army":
        current_amount = province_data["army"].get(item_name, 0)
    elif category == "weapons":
        current_amount = province_data["weapons"].get(item_name, 0)
    elif category == "structures":
        current_amount = province_data["structures"].get(item_name, 0)
    elif category == "misc":
        current_amount = province_data["misc"].get(item_name, 0)
    elif category == "goods":
        current_amount = province_data["economic_goods"].get(item_name, 0)
    elif category == "money":
        current_amount = province_data["wealth"]
    elif category == "population":
        current_amount = province_data["population"] // 2  # Max 50%
    else:
        current_amount = 0

    
    text = f"📦 انتقال {item_name}\n\n"
    text += f"موجودی فعلی: {current_amount:,}\n"
    text += f"مقصد: {user_data['transfer_target_country']} - {user_data['transfer_target_province']}\n\n"
    text += "تعداد مورد نظر را وارد کنید:"

    keyboard = [
        [InlineKeyboardButton("10", callback_data="transfer_qty_10"),
         InlineKeyboardButton("100", callback_data="transfer_qty_100"),
         InlineKeyboardButton("1000", callback_data="transfer_qty_1000")],
        [InlineKeyboardButton("25%", callback_data="transfer_qty_25p"),
         InlineKeyboardButton("50%", callback_data="transfer_qty_50p"),
         InlineKeyboardButton("همه", callback_data="transfer_qty_all")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")]
    ]
    

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def view_pending_transfers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    """View pending transfers for current user"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    
    # Push navigation state
    from utils import push_navigation_state
    push_navigation_state(user_data, "transfer_menu")

    try:
        transfers_data = load_pending_transfers()
        user_transfers = [
            t for t in transfers_data.get("transfers", []) 
            if t.get("requester_id") == user_id and t.get("status") == "pending"
        ]

        if not user_transfers:
            text = "📭 هیچ انتقالی در انتظار تأیید نیست."
            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")]]
        else:
            text = "🔄 انتقالات در انتظار تأیید شما:\n\n"
            for i, transfer in enumerate(user_transfers, 1):
                logger.warning(f"[DEBUG] Transfer ID: {transfer.get('id')} | Items: {transfer.get('items')} | Type: {type(transfer.get('items'))}")

                text += f"{i}. {transfer.get('source_country', 'نامشخص')} - {transfer.get('source_province', 'نامشخص')} → "
                text += f"{transfer.get('target_country', 'نامشخص')} - {transfer.get('target_province', 'نامشخص')}\n"

                items = transfer.get("items") or {}
                if isinstance(items, dict) and items:
                    for item_name, quantity in items.items():
                        text += f"   📦 {item_name} × {quantity:,}\n"
                else:
                    text += "   📦 آیتمی ثبت نشده\n"

                text += f"   🔄 نوع: {transfer.get('transfer_type', 'نامشخص')}\n"
                text += f"   📅 درخواست: {transfer.get('requested_at', 'نامشخص')[:10]}\n\n"


            keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")]]

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        logger.error(f"Error viewing pending transfers: {e}")
        await query.edit_message_text("❌ خطا در نمایش انتقالات در انتظار", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 برگشت", callback_data="transfer_menu")]
        ]))



async def handle_transfer_items_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user input for transfer items"""
    # user_id = update.message.from_user.id
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})

        # Ensure user_data dictionary exists for user_id
    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    user_data = context.user_data[user_id]

        # Check the correct step
    if user_data.get("step") != "awaiting_transfer_items_input":
        return

    
    text_input = update.message.text.strip()
    category = user_data.get("transfer_category")
    
    country = user_data["country"]
    province = user_data["province"]
    province_data = load_province_data(country, province)
    
    target_country = user_data["transfer_target_country"]
    target_province = user_data["transfer_target_province"]
    transfer_type = user_data["transfer_type"]
    
    # Parse input based on category
    transfer_items = {}
    validation_errors = []
    
    try:
        if category in ["economic_items", "army"]:
            # Parse format: "item: amount"
            lines = text_input.split('\n')
            for line in lines:
                if ':' in line:
                    item, amount = line.split(':', 1)
                    item = item.strip()
                    amount = int(amount.strip())
                    
                    # Validate availability
                    if category == "economic_items":
                        available = province_data.get("economic_items", {}).get(item, 0)
                    else:  # army
                        available = province_data.get("army", {}).get(item, 0)
                    
                    if available < amount:
                        validation_errors.append(f"❌ {item}: موجودی ناکافی (موجود: {available}, درخواستی: {amount})")
                    else:
                        transfer_items[item] = amount
                        
        elif category == "wealth":
            amount = int(text_input)
            available = province_data.get("wealth", 0)
            if available < amount:
                validation_errors.append(f"❌ ثروت ناکافی (موجود: {available}, درخواستی: {amount})")
            else:
                transfer_items["طلا"] = amount
                
        elif category == "population":
            amount = int(text_input)
            available = province_data.get("population", 0)
            max_transferable = available // 2
            if amount > max_transferable:
                validation_errors.append(f"❌ حداکثر قابل انتقال: {max_transferable} نفر")
            else:
                transfer_items["جمعیت"] = amount
                
        elif category in ["misc", "weapons", "structures"]:
            # Parse format: "item: count"
            lines = text_input.split('\n')
            available_items = province_data.get(category, [])
            
            for line in lines:
                if ':' in line:
                    item, count = line.split(':', 1)
                    item = item.strip()
                    count = int(count.strip())
                    
                    if item not in available_items:
                        validation_errors.append(f"❌ {item}: آیتم موجود نیست")
                    else:
                        transfer_items[item] = count
                        
    except ValueError:
        validation_errors.append("❌ فرمت ورودی نامعتبر")
    
    if validation_errors:
        error_text = "خطاهای زیر رخ داده:\n\n" + "\n".join(validation_errors)
        error_text += "\n\nلطفاً مجدداً تلاش کنید:"
        await update.message.reply_text(error_text)
        return True
    
    if not transfer_items:
        await update.message.reply_text("❌ هیچ آیتم معتبری وارد نشده. لطفاً مجدداً تلاش کنید:")
        return True
    
    # Store transfer items and show confirmation
    context.user_data[user_id]["transfer_items"] = transfer_items
    context.user_data[user_id]["step"] = "awaiting_transfer_confirmation"
    
    # Create confirmation message
    confirm_text = f"🔄 تأیید انتقال\n\n"
    confirm_text += f"📍 مبدأ: {country} - {province}\n"
    confirm_text += f"📍 مقصد: {target_country} - {target_province}\n"
    confirm_text += f"🔄 نوع: {'داخلی' if transfer_type == 'domestic' else 'بین‌المللی'}\n"
    confirm_text += f"📦 دسته‌بندی: {category}\n\n"
    confirm_text += "آیتم‌های انتقال:\n"
    
    for item, amount in transfer_items.items():
        confirm_text += f"• {item}: {amount:,}\n"
    
    confirm_text += "\n⚠️ پس از تأیید، درخواست برای بررسی ادمین ارسال می‌شود."
    
    keyboard = [
        [InlineKeyboardButton("✅ تأیید انتقال", callback_data="confirm_transfer_request"),
         InlineKeyboardButton("❌ انصراف", callback_data="transfer_menu")]
    ]
    
    await update.message.reply_text(confirm_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return True

async def process_transfer_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process transfer request and send for admin approval"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # 🧠 بررسی اینکه اطلاعات ضروری وجود دارند
    country = user_data.get("country")
    province = user_data.get("province")
    transfer_target_country = user_data.get("transfer_target_country")
    transfer_target_province = user_data.get("transfer_target_province")
    transfer_type = user_data.get("transfer_type")
    transfer_items = user_data.get("transfer_items", {})
    category = user_data.get("transfer_category")

    if not all([country, province, transfer_target_country, transfer_target_province, transfer_type, category, transfer_items]):
        await query.answer("⚠️ داده‌های انتقال ناقص است. لطفاً از ابتدا مراحل را طی کنید.", show_alert=True)
        return

    # 📦 ساخت درخواست انتقال
    transfer_request = {
        "id": f"transfer_{user_id}_{int(datetime.utcnow().timestamp())}",
        "requester_id": user_id,
        "source_country": country,
        "source_province": province,
        "target_country": transfer_target_country,
        "target_province": transfer_target_province,
        "transfer_type": transfer_type,
        "category": category,
        "items": transfer_items,
        "status": "pending",
        "requested_at": datetime.utcnow().isoformat(),
        "delay_until": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }

    # 💾 ذخیره در فایل انتقال‌های در انتظار
    transfers_data = load_pending_transfers()
    transfers_data.setdefault("transfers", []).append(transfer_request)
    save_pending_transfers(transfers_data)

    # 👑 ارسال به ادمین‌ها برای تایید
    from config import COUNTRY_ADMIN_ID
    target_country = transfer_target_country
    admins = COUNTRY_ADMIN_ID.get(target_country, [])

    admin_text = (
        f"🔄 درخواست انتقال جدید\n\n"
        f"👤 درخواست‌کننده: {user_id}\n"
        f"🌍 مبدأ: {country} - {province}\n"
        f"🎯 مقصد: {transfer_target_country} - {transfer_target_province}\n"
        f"🚚 نوع: {'داخلی' if transfer_type == 'domestic' else 'بین‌المللی'}\n"
        f"🏷️ دسته‌بندی: {category}\n\n"
        f"آیتم‌ها:\n" +
        "".join([f"• {item}: {amount:,}\n" for item, amount in transfer_items.items()])
    )

    admin_keyboard = [[
        InlineKeyboardButton("✅ تایید", callback_data=f"approve_transfer_{transfer_request['id']}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_transfer_{transfer_request['id']}")
    ]]

    if not admins:
        logger.warning(f"No admins found for country {target_country}, transfer id: {transfer_request['id']}")
    else:
        for admin_id in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    reply_markup=InlineKeyboardMarkup(admin_keyboard)
                )
            except Exception as e:
                logger.error(f"Could not send message to admin {admin_id}: {e}")

    # 📩 تأیید برای کاربر
    text = (
        f"✅ درخواست انتقال ثبت شد!\n\n"
        f"🎯 مقصد: {transfer_target_country} - {transfer_target_province}\n"
        f"🏷️ دسته‌بندی: {category}\n\n"
        "آیتم‌ها:\n" +
        "".join([f"• {item}: {amount:,}\n" for item, amount in transfer_items.items()]) +
        "\n⏳ انتقال پس از تأیید ادمین اجرا خواهد شد."
    )

    keyboard = [[InlineKeyboardButton("🏠 برگشت به منو", callback_data="country_overview")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # 🧹 پاکسازی داده‌های موقت کاربر
    for key in [
        "transfer_target_country",
        "transfer_target_province",
        "transfer_type",
        "transfer_category",
        "transfer_items",
        "step",
    ]:
        user_data.pop(key, None)

