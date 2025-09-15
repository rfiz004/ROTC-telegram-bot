"""
Shop handler module - handles shop functionality with local JSON storage
"""
import logging
import json
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden
from keyboards import back_and_home_buttons
from config import SHOP_CHANNEL
from province_handler import load_province_data, save_province_data
from admin_province_handler import is_shop_blocked_for_user

logger = logging.getLogger(__name__)

SHOP_ITEMS_FILE = "shop_items.json"

def load_shop_items():
    """Load shop items from local JSON file"""
    if not os.path.exists(SHOP_ITEMS_FILE):
        return []

    try:
        with open(SHOP_ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading shop items: {e}")
        return []

def save_shop_items(items):
    """Save shop items to local JSON file"""
    try:
        with open(SHOP_ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(items)} shop items to {SHOP_ITEMS_FILE}")
    except Exception as e:
        logger.error(f"Error saving shop items: {e}")

def add_shop_item(item_data):
    """Add a new item to the shop with numeric ID"""
    try:
        # Load existing items
        items = load_shop_items()

        # Generate numeric ID
        existing_ids = [int(item.get("id", 0)) for item in items if str(item.get("id", "")).isdigit()]
        next_id = max(existing_ids) + 1 if existing_ids else 1

        # Set ID and timestamp
        item_data["id"] = str(next_id)  # ذخیره به‌صورت رشته برای یکدستی
        item_data["created_at"] = datetime.utcnow().isoformat()

        # Add to items list
        items.append(item_data)

        # Save to file
        save_shop_items(items)

        return item_data["id"]

    except Exception as e:
        logger.error(f"Error adding shop item: {e}")
        return None


# def filter_items_by_country(items, user_country):
#     """Filter items by user's country - include 'All' country items"""
#     filtered = []
#     for item in items:
#         item_country = item.get("country", "All")
#         if item_country == "All" or item_country.lower() == user_country.lower():
#             filtered.append(item)
#     return filtered

def filter_items_by_country(items, user_country):
    """Filter items by user's country (supports multiple countries per item)"""
    filtered = []
    for item in items:
        item_countries = item.get("countries") or [item.get("country", "All")]

        # اطمینان از اینکه لیست است
        if isinstance(item_countries, str):
            item_countries = [item_countries]

        # چک کردن وجود کشور کاربر یا All
        item_countries_lower = [c.lower() for c in item_countries]
        if "all" in item_countries_lower or user_country.lower() in item_countries_lower:
            filtered.append(item)
    return filtered


# shop_handler.py
def delete_shop_item(item_id):
    try:
        items = load_shop_items()

        def id_matches(item_id_in_list, target):
            if item_id_in_list is None:
                return False
            # direct equal (handles same type)
            if item_id_in_list == target:
                return True
            # compare as strings
            if str(item_id_in_list) == str(target):
                return True
            # If stored id like "item_123" and target is "123" or 123, match tail
            try:
                if isinstance(item_id_in_list, str) and "_" in item_id_in_list:
                    tail = item_id_in_list.split("_")[-1]
                    if str(target) == tail:
                        return True
            except Exception:
                pass
            return False

        new_items = []
        deleted = False
        for it in items:
            if id_matches(it.get("id"), item_id):
                deleted = True
                continue
            new_items.append(it)

        if not deleted:
            logger.warning(f"Shop item not found for deletion: {item_id}")
            return False

        save_shop_items(new_items)
        logger.info(f"Deleted shop item: {item_id}")
        return True

    except Exception as e:
        logger.exception("Error in delete_shop_item: %s", e)
        return False


def update_shop_item(item_id, updates):
    """Update a shop item"""
    try:
        items = load_shop_items()

        for item in items:
            # مقایسه به صورت رشته تا مشکل نوع (int/str) حل شود
            if str(item.get('id')) == str(item_id):
                item.update(updates)
                item['updated_at'] = datetime.utcnow().isoformat()
                save_shop_items(items)
                logger.info(f"Updated shop item: {item_id}")
                return True

        # اگر به انتها رسیدیم یعنی آیتم پیدا نشد
        logger.warning(f"Shop item not found for update: {item_id}")
        return False

    except Exception as e:
        logger.error(f"Error updating shop item {item_id}: {e}", exc_info=True)
        return False


def filter_items_by_category(items, category):
    """Filter items by category/type"""
    filtered = []
    for item in items:
        item_type = item.get("type", "Misc").lower()
        if item_type == category.lower():
            filtered.append(item)
    return filtered

def filter_items_by_hashtag(items, hashtag):
    """Filter items by hashtag"""
    filtered = []
    hashtag = hashtag.lower()
    for item in items:
        item_hashtags = [tag.lower() for tag in item.get("hashtags", [])]
        if hashtag in item_hashtags:
            filtered.append(item)
    return filtered

def count_items_by_category(items):
    """Count items by category for display"""
    categories = {}
    for item in items:
        cat = item.get("type", "Misc").lower()
        categories[cat] = categories.get(cat, 0) + 1
    return categories

async def open_shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open shop main menu with accurate item counts"""
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    # Get user's country
    country = user_data.get("country")
    if not country:
        await update.callback_query.edit_message_text(
            "❌ ابتدا وارد کشور شوید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
            ]])
        )
        return

    # Show loading message
    # await update.callback_query.edit_message_text("🔄 در حال بارگذاری فروشگاه...")
    try:
        await update.callback_query.message.delete()
    except Exception as e:
        # اگر حذف پیام خطا داد، اینجا هندل کن یا ردش کن
            print(f"Error deleting message: {e}")
        
    await context.bot.send_message(
        chat_id=update.callback_query.message.chat.id,
        text="🔄 در حال بارگذاری فروشگاه..."
    )



    # Load all items from JSON file
    all_items = load_shop_items()

    # Filter items for user's country
    user_items = filter_items_by_country(all_items, country)

    # Store items in user data for later use
    context.user_data[user_id]["shop_items"] = user_items
    context.user_data[user_id]["all_shop_items"] = all_items

    # Count items by category for this user's country
    categories = count_items_by_category(user_items)

    # Category names mapping
    category_names = {
        "army": "⚔️ ارتش",
        "castle": "🏰 قلعه", 
        "structure": "🏗 سازه",
        "weapon": "🗡 سلاح",
        "misc": "📦 متفرقه",
        "econstructure": "🏭 اقتصادی"
    }

    # Create category buttons with accurate counts
    buttons = []

    # Row 1: Army and Castle
    row1 = [
        InlineKeyboardButton(
            f"{category_names['army']} ({categories.get('army', 0)})", 
            callback_data="shop_category_army"
        ),
        InlineKeyboardButton(
            f"{category_names['castle']} ({categories.get('castle', 0)})", 
            callback_data="shop_category_castle"
        )
    ]
    buttons.append(row1)

    # Row 2: Structure and Weapon
    row2 = [
        InlineKeyboardButton(
            f"{category_names['structure']} ({categories.get('structure', 0)})", 
            callback_data="shop_category_structure"
        ),
        InlineKeyboardButton(
            f"{category_names['weapon']} ({categories.get('weapon', 0)})", 
            callback_data="shop_category_weapon"
        )
    ]
    buttons.append(row2)

    # Row 3: Misc and Economic
    row3 = [
        InlineKeyboardButton(
            f"{category_names['misc']} ({categories.get('misc', 0)})", 
            callback_data="shop_category_misc"
        ),
        InlineKeyboardButton(
            f"{category_names['econstructure']} ({categories.get('econstructure', 0)})", 
            callback_data="shop_category_econstructure"
        )
    ]
    buttons.append(row3)

    # Back button
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_country_menu")])

    try:
        await update.callback_query.message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")
    
    await context.bot.send_message(
    chat_id=update.callback_query.message.chat.id,
    text=f"🏪 به فروشگاه خوش آمدید!\n📦 {len(user_items)} آیتم موجود برای کشور {country}\n\nدسته مورد نظر را انتخاب کنید:",
    reply_markup=InlineKeyboardMarkup(buttons)
)

    # await update.callback_query.edit_message_text(
    #     f"🏪 به فروشگاه خوش آمدید!\n📦 {len(user_items)} آیتم موجود برای کشور {country}\n\nدسته مورد نظر را انتخاب کنید:",
    #     reply_markup=InlineKeyboardMarkup(buttons)
    # )

# async def show_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Show items in selected category with navigation"""
#     query = update.callback_query
#     await query.answer()

#     category = query.data.split("_")[-1]  # Extract category from callback data
#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     country = user_data.get("country", "")

#     # Get filtered items for this category
#     all_items = user_data.get("shop_items", [])
#     category_items = filter_items_by_category(all_items, category)

#     if not category_items:
#         category_names = {
#             "army": "⚔️ ارتش",
#             "castle": "🏰 قلعه",
#             "structure": "🏗 سازه", 
#             "weapon": "🗡 سلاح",
#             "misc": "📦 متفرقه",
#             "econstructure": "🏭 سازه‌های اقتصادی"
#         }

#         await query.edit_message_text(
#             f"📭 هیچ آیتمی در دسته {category_names.get(category, category)} برای کشور {country} یافت نشد.",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")
#             ]])
#         )
#         return

#     # Store category items and initialize pagination
#     context.user_data[user_id]["category_items"] = category_items
#     context.user_data[user_id]["current_category"] = category
#     context.user_data[user_id]["current_page"] = 0

#     # Show first page
#     await show_items_page(query, context, user_id, 0, category)

# async def show_items_page(query, context, user_id, page, category):
#     """Show single item per page with navigation buttons"""
#     user_data = context.user_data.get(user_id, {})
#     category_items = user_data.get("category_items", [])

#     if not category_items:
#         await query.edit_message_text(
#             "📭 هیچ آیتمی یافت نشد.",
#             reply_markup=InlineKeyboardMarkup([[
#                 InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")
#             ]])
#         )
#         return

#     # Calculate pagination
#     total_items = len(category_items)
#     page = max(0, min(page, total_items - 1))
#     current_item = category_items[page]

#     # Update current page in user data
#     context.user_data[user_id]["current_page"] = page

#     # Build formatted item display
#     page_info = f"🛍 آیتم {page + 1} از {total_items}\n\n"

#     # Build the item caption
#     caption = f"──────⊱◈Shop◈⊰──────\n"
#     caption += f"✦ Item Name : {current_item.get('name', 'نامشخص')}\n"
#     caption += f"✧ Item Type : {current_item.get('type', 'Misc')}\n"
#     caption += f"✦ Country : {current_item.get('country', 'All')}\n"

#     # Add hashtags
#     hashtags = current_item.get('hashtags', [])
#     for hashtag in hashtags:
#         caption += f"{hashtag}\n"

#     caption += f"✧ Description :\n"
#     caption += f"• {current_item.get('description', 'توضیحات موجود نیست')}"
    
#     # اضافه کردن تعداد برای دسته‌های مشخص
#     count = current_item.get("count", 1)
#     item_type = current_item.get("type", "").lower()
    
#     if item_type in ["army", "castle", "misc", "structure", "weapon"]:
#         caption += f"\n✦ تعداد موجود: {count}"


#     caption += f"✦ Price & Materials :\n"
#     caption += f"• {current_item.get('price', 0):,}"

#     materials = current_item.get('materials', {})
#     if materials:
#         material_parts = []
#         for material, amount in materials.items():
#             material_parts.append(f"{material}:{amount}")
#         caption += f", {', '.join(material_parts)}"

#     caption += f"\n✧ Owner ID : {current_item.get('owner', 'نامشخص')}\n"
#     caption += f"──────⊹⊱✫⊰⊹──────\n"
#     caption += f"https://t.me/R_O_T_C\n"
#     caption += f"https://t.me/R_O_T_C_Shop"

#     full_caption = page_info + caption

#     # Create navigation buttons
#     nav_buttons = []
#     if total_items > 1:
#         # Previous button (disabled if first page)
#         if page > 0:
#             prev_btn = InlineKeyboardButton("⬅️ قبلی", callback_data=f"shop_page_{category}_{page-1}")
#         else:
#             prev_btn = InlineKeyboardButton("⬅️", callback_data="noop")

#         # Next button (disabled if last page)  
#         if page < total_items - 1:
#             next_btn = InlineKeyboardButton("➡️ بعدی", callback_data=f"shop_page_{category}_{page+1}")
#         else:
#             next_btn = InlineKeyboardButton("➡️", callback_data="noop")

#         nav_buttons = [prev_btn, next_btn]

#     # Build keyboard
#     keyboard = []
#     if nav_buttons:
#         keyboard.append(nav_buttons)

#     keyboard.extend([
#         [InlineKeyboardButton("🛒 خرید", callback_data=f"buy_item_{category}_{page}")],
#         [InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")]
#     ])

#     # Get photo file_id
#     photo_file_id = current_item.get('photo_file_id')

#     try:
#         # Try to send with photo first
#         if photo_file_id:
#             try:
#                 await query.delete_message()
#                 await context.bot.send_photo(
#                     chat_id=query.message.chat_id,
#                     photo=photo_file_id,
#                     caption=full_caption,
#                     reply_markup=InlineKeyboardMarkup(keyboard),
#                     parse_mode=None  # No parsing to preserve original formatting
#                 )
#                 return
#             except Exception as photo_error:
#                 logger.error(f"Error sending photo {photo_file_id}: {photo_error}")

#         # Fallback to text message
#         try:
#             # await query.edit_message_text(
#             #     text=full_caption,
#             #     reply_markup=InlineKeyboardMarkup(keyboard),
#             #     parse_mode=None  # Preserve original formatting
#             # )
#             await context.bot.send_message(
#                 chat_id=query.message.chat.id,
#                 text=full_caption,
#                 reply_markup=InlineKeyboardMarkup([...])
#             )
#         except Exception as edit_error:
#             logger.error(f"Error editing message: {edit_error}")
#             # Last resort - send new message
#             try: 
#                 await query.delete_message()
#             except:
#                 pass
#             await context.bot.send_message(
#                 chat_id=query.message.chat_id,
#                 text=full_caption,
#                 reply_markup=InlineKeyboardMarkup(keyboard),
#                 parse_mode=None
#             )

#     except Exception as e:
#         logger.error(f"Error displaying item: {e}")
#         # Emergency fallback
#         try:
#             fallback_text = f"❌ خطا در نمایش آیتم\n🛍 آیتم {page + 1} از {total_items}\n📦 {current_item.get('name', 'نامشخص')}"
#             await query.edit_message_text(
#                 fallback_text,
#                 reply_markup=InlineKeyboardMarkup(keyboard)
#             )
#         except:
#             pass


# async def show_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Show items in selected category with navigation"""
#     query = update.callback_query
#     await query.answer()

#     category = query.data.split("_")[-1]  # Extract category from callback data
#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     user_country = user_data.get("country", "")

#     # Get all shop items (آپدیت شده)
#     all_items = user_data.get("shop_items", [])

#     # Filter by category AND user country
#     category_items = [
#         item for item in all_items
#         if filter_items_by_category([item], category) and
#            ("countries" in item and user_country in item["countries"])
#     ]

#     if not category_items:
#         category_names = {
#             "army": "⚔️ ارتش",
#             "castle": "🏰 قلعه",
#             "structure": "🏗 سازه",
#             "weapon": "🗡 سلاح",
#             "misc": "📦 متفرقه",
#             "econstructure": "🏭 سازه‌های اقتصادی"
#         }
#         await query.edit_message_text(
#             f"📭 هیچ آیتمی در دسته {category_names.get(category, category)} برای کشور {user_country} یافت نشد.",
#             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")]])
#         )
#         return

#     # Store filtered category items & init pagination
#     context.user_data[user_id]["category_items"] = category_items
#     context.user_data[user_id]["current_category"] = category
#     context.user_data[user_id]["current_page"] = 0

#     # Show first page
#     await show_items_page(query, context, user_id, 0, category)


async def show_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show items in selected category with navigation"""
    query = update.callback_query
    await query.answer()

    category = query.data.split("_")[-1]  # Extract category from callback data
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})
    user_country = user_data.get("country", "")

    # Get all shop items (آپدیت شده)
    all_items = user_data.get("shop_items", [])

    # اول فیلتر دسته
    category_items = filter_items_by_category(all_items, category)

    # بعد فیلتر کشور (پشتیبانی از country و countries + All)
    category_items = filter_items_by_country(category_items, user_country)

    if not category_items:
        category_names = {
            "army": "⚔️ ارتش",
            "castle": "🏰 قلعه",
            "structure": "🏗 سازه",
            "weapon": "🗡 سلاح",
            "misc": "📦 متفرقه",
            "econstructure": "🏭 سازه‌های اقتصادی"
        }
        await query.edit_message_text(
            f"📭 هیچ آیتمی در دسته {category_names.get(category, category)} برای کشور {user_country} یافت نشد.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")]]
            )
        )
        return

    # Store filtered category items & init pagination
    context.user_data[user_id]["category_items"] = category_items
    context.user_data[user_id]["current_category"] = category
    context.user_data[user_id]["current_page"] = 0

    # Show first page
    await show_items_page(query, context, user_id, 0, category)


async def show_items_page(query, context, user_id, page, category):
    """Show single item per page with navigation buttons"""
    user_data = context.user_data.get(user_id, {})
    category_items = user_data.get("category_items", [])

    if not category_items:
        await query.edit_message_text(
            "📭 هیچ آیتمی یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")]])
        )
        return

    total_items = len(category_items)
    page = max(0, min(page, total_items - 1))
    current_item = category_items[page]

    context.user_data[user_id]["current_page"] = page

    # Build caption
    caption = f"──────⊱◈Shop◈⊰──────\n"
    caption += f"✦ Item Name : {current_item.get('name', 'نامشخص')}\n"
    caption += f"✧ Item Type : {current_item.get('type', 'Misc')}\n"
    caption += f"✦ Country : {current_item.get('country', 'All')}\n"
    caption += "\n".join(current_item.get("hashtags", [])) + "\n"
    caption += f"✧ Description :\n• {current_item.get('description', 'توضیحات موجود نیست')}\n"
    
    count = current_item.get("count", 1)
    item_type = current_item.get("type", "").lower()
    if item_type in ["army", "castle", "misc", "structure", "weapon"]:
        caption += f"✦ تعداد موجود: {count}\n"

    caption += f"✦ Price & Materials :\n• {current_item.get('price', 0):,}"
    materials = current_item.get("materials", {})
    if materials:
        caption += ", " + ", ".join(f"{k}:{v}" for k, v in materials.items())

    caption += f"\n✧ Owner ID : {current_item.get('owner', 'نامشخص')}\n"
    caption += f"──────⊹⊱✫⊰⊹──────\n"
    caption += f"https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Shop"

    page_info = f"🛍 آیتم {page + 1} از {total_items}\n\n"
    full_caption = page_info + caption

    # Navigation buttons
    nav_buttons = []
    if total_items > 1:
        prev_btn = InlineKeyboardButton("⬅️ قبلی", callback_data=f"shop_page_{category}_{page-1}") if page > 0 else InlineKeyboardButton("⬅️", callback_data="noop")
        next_btn = InlineKeyboardButton("➡️ بعدی", callback_data=f"shop_page_{category}_{page+1}") if page < total_items - 1 else InlineKeyboardButton("➡️", callback_data="noop")
        nav_buttons.append([prev_btn, next_btn])

    keyboard = nav_buttons + [
        [InlineKeyboardButton("🛒 خرید", callback_data=f"buy_item_{category}_{page}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")]
    ]

    # Send new message (delete previous)
    try:
        await query.delete_message()
    except:
        pass

    photo_file_id = current_item.get("photo_file_id")
    if photo_file_id:
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=photo_file_id,
            caption=full_caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=full_caption,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def show_shop_items_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop item pagination from callback"""
    query = update.callback_query
    await query.answer()

    # Parse callback data: shop_page_{category}_{page}
    data_parts = query.data.replace("shop_page_", "").split("_")

    if len(data_parts) < 2:
        await query.edit_message_text("❌ خطا در صفحه‌بندی.", reply_markup=back_and_home_buttons())
        return

    category = data_parts[0]

    try:
        page = int(data_parts[1])
    except ValueError:
        await query.edit_message_text("❌ شماره صفحه نامعتبر.", reply_markup=back_and_home_buttons())
        return

    user_id = query.from_user.id
    await show_items_page(query, context, user_id, page, category)

async def handle_item_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    """Handle item purchase initiation"""
    query = update.callback_query
    await query.answer()

    # Parse callback data: buy_item_{category}_{page_index}
    purchase_data = query.data.replace("buy_item_", "")
    parts = purchase_data.split("_")

    if len(parts) < 2:
        await context.bot.send_message("❌ خطا در خرید.", reply_markup=back_and_home_buttons())
        return

    category = parts[0]
    page_index = int(parts[1])

    user_id = query.from_user.id
    user_data = context.user_data.setdefault(user_id, {})  # ✅ اگه نبود، ایجاد میشه
    # فرض: تابعی برای گرفتن استان کاربر داری مثل get_user_province(user_id)
    province = user_data.get("province")  # این تابع باید از دیتابیس یا فایل دیتا کاربر مقدار رو بگیره

    if is_shop_blocked_for_user(province):
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🚫 فروشگاه برای کشور شما قفل است و امکان خرید وجود ندارد.",
            reply_markup=back_and_home_buttons()
        )
        return


    category_items = user_data.get("category_items", [])

    if page_index >= len(category_items):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ کالا پیدا نشد.",
            reply_markup=back_and_home_buttons()
        )
        return

    item = category_items[page_index]

    # ✅ Set purchase info directly in context.user_data
    context.user_data[user_id].update({
        "purchase_item": item,
        "category": category,
        "step": "awaiting_quantity",
        "flow_type": "shop_purchase"
    })
    print(f"[DEBUG] handle_item_purchase triggered by user {user_id}")

    # text = f"🛒 **خرید {item['name']}**\n\n"
    # text += f"💰 قیمت واحد: {item['price']:,} طلا\n"

    # if item.get('materials'):
    #     text += "🔧 مواد مورد نیاز (برای هر واحد):\n"
    #     for material, amount in item['materials'].items():
    #         text += f"   • {material}: {amount}\n"

    # text += "\n🔢 تعداد مورد نظر را وارد کنید:"
    text = f"🛒 **خرید {item['name']}**\n\n"
    text += f"💰 قیمت واحد: {item['price']:,} طلا\n"
    
    if item.get('materials'):
        text += "🔧 مواد مورد نیاز (برای هر واحد):\n"
        for material, amount in item['materials'].items():
            text += f"   • {material}: {amount}\n"
    
    # اضافه کردن تعداد موجود
    item_type = item.get("type", "").lower()
    if item_type in ["army", "castle", "misc", "structure", "weapon"]:
        count = item.get("count", 1)
        text += f"\n✦ تعداد موجود: {count}\n"
    
    text += "\n🔢 تعداد مورد نظر را وارد کنید:"


    keyboard = [
        [InlineKeyboardButton("🔙 برگشت", callback_data=f"shop_category_{category}")]
    ]

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )




# async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle quantity input from user"""
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     if user_data.get("step") != "awaiting_quantity" or user_data.get("flow_type") != "shop_purchase":
#         return False

#     try:
#         quantity = int(update.message.text.strip())
#         if quantity <= 0:
#             await update.message.reply_text("❌ تعداد باید عدد مثبت باشد.")
#             return True

#         if quantity > 1000:
#             await update.message.reply_text("❌ حداکثر تعداد مجاز 1000 است.")
#             return True

#     except ValueError:
#         await update.message.reply_text("❌ لطفاً عدد معتبر وارد کنید.")
#         return True

#     item = user_data.get("purchase_item")
#     if not item:
#         await update.message.reply_text("❌ خطا در خرید.", reply_markup=back_and_home_buttons())
#         return True

#     # Validate resources
#     country = user_data.get("country")
#     province = user_data.get("province")

#     if not country or not province:
#         await update.message.reply_text("❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
#         return True

#     province_data = load_province_data(country, province)
#     if not province_data:
#         await update.message.reply_text("❌ خطا در بارگذاری اطلاعات استان.", reply_markup=back_and_home_buttons())
#         return True

#     total_price = item["price"] * quantity
#     total_materials = {}
#     for material, amount in item.get("materials", {}).items():
#         total_materials[material] = amount * quantity

#     # Check gold
#     if province_data.get("wealth", 0) < total_price:
#         shortage = total_price - province_data.get("wealth", 0)
#         await update.message.reply_text(
#             f"❌ طلای کافی ندارید!\n\n"
#             f"💰 مورد نیاز: {total_price:,} طلا\n"
#             f"💰 موجودی: {province_data.get('wealth', 0):,} طلا\n"
#             f"❌ کمبود: {shortage:,} طلا"
#         )
#         return True

    
#     # Store final data for confirmation
#     context.user_data[user_id]["purchase_quantity"] = quantity
#     context.user_data[user_id]["total_price"] = total_price
#     context.user_data[user_id]["total_materials"] = total_materials

#     text = f"🛒 **تأیید نهایی خرید**\n\n"
#     text += f"📦 کالا: {item['name']}\n"
#     text += f"🔢 تعداد: {quantity:,}\n"
#     text += f"💰 قیمت کل: {total_price:,} طلا\n"

#     if total_materials:
#         text += "\n🔧 مواد مصرفی:\n"
#         for material, amount in total_materials.items():
#             text += f"   • {material}: {amount:,}\n"

#     text += "\n✅ آیا مطمئن هستید؟"

#     keyboard = [
#         [InlineKeyboardButton("✅ تأیید خرید", callback_data="confirm_purchase")],
#         [InlineKeyboardButton("❌ لغو", callback_data=f"shop_category_{user_data.get('category', '')}")]
#     ]

#     await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
#     return True


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity input from user"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})

    if user_data.get("step") != "awaiting_quantity" or user_data.get("flow_type") != "shop_purchase":
        return False

    try:
        quantity = int(update.message.text.strip())
        if quantity <= 0:
            await update.message.reply_text("❌ تعداد باید عدد مثبت باشد.")
            return True

        if quantity > 1000:
            await update.message.reply_text("❌ حداکثر تعداد مجاز 1000 است.")
            return True

    except ValueError:
        await update.message.reply_text("❌ لطفاً عدد معتبر وارد کنید.")
        return True

    item = user_data.get("purchase_item")
    if not item:
        await update.message.reply_text("❌ خطا در خرید.", reply_markup=back_and_home_buttons())
        return True

    # Load province data
    country = user_data.get("country")
    province = user_data.get("province")

    if not country or not province:
        await update.message.reply_text("❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
        return True

    province_data = load_province_data(country, province)
    if not province_data:
        await update.message.reply_text("❌ خطا در بارگذاری اطلاعات استان.", reply_markup=back_and_home_buttons())
        return True

    # Calculate total price
    total_price = item["price"] * quantity

    # Check gold
    if province_data.get("wealth", 0) < total_price:
        shortage = total_price - province_data.get("wealth", 0)
        await update.message.reply_text(
            f"❌ طلای کافی ندارید!\n\n"
            f"💰 مورد نیاز: {total_price:,} طلا\n"
            f"💰 موجودی: {province_data.get('wealth', 0):,} طلا\n"
            f"❌ کمبود: {shortage:,} طلا"
        )
        return True

    # Check all materials using the helper function
    missing_materials = check_materials(province_data, item, quantity)
    if missing_materials:
        msg = "❌ مواد کافی موجود نیست:\n"
        for mat, amt in missing_materials.items():
            msg += f"   • {mat}: کمبود {amt}\n"
        await update.message.reply_text(msg, reply_markup=back_and_home_buttons())
        return True

    # Store final data for confirmation
    total_materials = {mat: amt * quantity for mat, amt in item.get("materials", {}).items()}
    context.user_data[user_id]["purchase_quantity"] = quantity
    context.user_data[user_id]["total_price"] = total_price
    context.user_data[user_id]["total_materials"] = total_materials

    # Prepare confirmation text
    text = f"🛒 **تأیید نهایی خرید**\n\n"
    text += f"📦 کالا: {item['name']}\n"
    text += f"🔢 تعداد: {quantity:,}\n"
    text += f"💰 قیمت کل: {total_price:,} طلا\n"

    if total_materials:
        text += "\n🔧 مواد مصرفی:\n"
        for material, amount in total_materials.items():
            text += f"   • {material}: {amount:,}\n"

    text += "\n✅ آیا مطمئن هستید؟"

    keyboard = [
        [InlineKeyboardButton("✅ تأیید خرید", callback_data="confirm_purchase")],
        [InlineKeyboardButton("❌ لغو", callback_data=f"shop_category_{user_data.get('category', '')}")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return True



def check_materials(province_data, item, quantity):
    """
    بررسی مواد مورد نیاز و موجودی استان.
    بر اساس کل موجودی از همه‌ی بخش‌ها جمع می‌کند و سپس مقایسه می‌کند.
    """
    missing = {}
    for mat, required in item.get("materials", {}).items():
        total_required = required * quantity
        total_available = 0

        # جمع موجودی از همه‌ی بخش‌های اصلی
        sections = ["army", "castle", "structures", "weapons", "misc", "economic_items"]
        for section_name in sections:
            section = province_data.get(section_name, {})
            total_available += section.get(mat, 0)

        # محصولات ساختارهای اقتصادی
        for es_data in province_data.get("economic_structures", {}).values():
            if es_data.get("product") == mat:
                total_available += es_data.get("count", 0) * es_data.get("weekly_output", 0)

        # اگر موجودی کافی نبود → کمبود
        if total_available < total_required:
            missing[mat] = total_required - total_available

    return missing



# def check_materials(province_data, item, quantity):
#     missing = {}
#     for mat, required in item.get("materials", {}).items():
#         total_required = required * quantity
#         found = False

#         # Army
#         if mat in province_data.get("army", {}):
#             if province_data["army"][mat] < total_required:
#                 missing[mat] = total_required - province_data["army"][mat]
#             found = True

#         # Castle, Structures, Weapons, Misc
#         for key in ["castle", "structures", "weapons", "misc"]:
#             section = province_data.get(key, {})
#             if mat in section:
#                 if section[mat] < total_required:
#                     missing[mat] = total_required - section[mat]
#                 found = True

#         # Economic items
#         if mat in province_data.get("economic_items", {}):
#             if province_data["economic_items"][mat] < total_required:
#                 missing[mat] = total_required - province_data["economic_items"][mat]
#             found = True

#         # Economic structures
#         for es_name, es_data in province_data.get("economic_structures", {}).items():
#             if es_data.get("product") == mat:
#                 available = es_data.get("count", 0) * es_data.get("weekly_output", 0)
#                 if available < total_required:
#                     missing[mat] = total_required - available
#                 found = True

#         if not found:
#             # Material not found anywhere
#             missing[mat] = total_required

#     return missing


# async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     print(f"[DEBUG] confirm_purchase triggered by user {user_id}")
#     """Confirm and process the purchase"""
#     query = update.callback_query
#     await query.answer()

#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     item = user_data.get("purchase_item")
#     quantity = user_data.get("purchase_quantity", 1)
#     total_price = user_data.get("total_price", 0)
#     total_materials = user_data.get("total_materials", {})

#     if not item:
#         await context.bot.send_message("❌ خطا در خرید.", reply_markup=back_and_home_buttons())
#         return

#     # Get province data
#     country = user_data.get("country")
#     province = user_data.get("province")

#     if not country or not province:
#         await context.bot.send_message("❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
#         return

#     province_data = load_province_data(country, province)
#     if not province_data:
#         from province_handler import create_new_province
#         province_data = create_new_province(country, province)

#     # Deduct resources
#     province_data["wealth"] -= total_price

#     # Add item to appropriate category
#     item_name = item["name"]
#     item_type = item.get("type", "misc").lower()

#     if item_type == "army":
#         if "army" not in province_data:
#             province_data["army"] = {}
#         province_data["army"][item_name] = province_data["army"].get(item_name, 0) + quantity
#         province_data["total_army"] = province_data.get("total_army", 0) + quantity

#     elif item_type == "weapon":
#         if "weapons" not in province_data:
#             province_data["weapons"] = []
#         for i in range(quantity):
#             province_data["weapons"].append(item_name)

#     elif item_type == "castle":
#         if "castle" not in province_data:
#             province_data["castle"] = []
#         for i in range(quantity):
#             province_data["castle"].append(item_name)

#     elif item_type == "structure":
#         if "structures" not in province_data:
#             province_data["structures"] = []
#         for i in range(quantity):
#             province_data["structures"].append(item_name)

#     elif item_type == "econstructure":
#         if "economic_structures" not in province_data:
#             province_data["economic_structures"] = {}
#         province_data["economic_structures"][item_name] = province_data["economic_structures"].get(item_name, 0) + quantity
#     else:
#         if "misc" not in province_data:
#             province_data["misc"] = []
#         for i in range(quantity):
#             province_data["misc"].append(item_name)

#     # Save updated data
#     save_province_data(country, province, province_data)

#     # Clear purchase data
#     for key in ["purchase_item", "purchase_quantity", "total_price", "total_materials", "step", "flow_type"]:
#         context.user_data[user_id].pop(key, None)

#     text = f"✅ خرید با موفقیت انجام شد!\n\n"
#     text += f"📦 {item_name} × {quantity:,} به استان شما اضافه شد.\n"
#     text += f"💰 طلای باقی‌مانده: {province_data['wealth']:,} طلا"

#     keyboard = [
#         [InlineKeyboardButton("🏠 نمایش استان", callback_data="country_overview")],
#         [InlineKeyboardButton("🛒 ادامه خرید", callback_data="open_shop")]
#     ]

#     await context.bot.send_message(
#         chat_id=query.message.chat_id,
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )


# async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     with open("economic_structures.json", "r", encoding="utf-8") as f:
#         all_econ_structs = json.load(f)

#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     item = user_data.get("purchase_item")
#     quantity = user_data.get("purchase_quantity", 1)
#     total_price = user_data.get("total_price", 0)
#     total_materials = user_data.get("total_materials", {})

#     if not item:
#         await context.bot.send_message(user_id, "❌ خطا در خرید.", reply_markup=back_and_home_buttons())
#         return

#     country = user_data.get("country")
#     province = user_data.get("province")

#     if not country or not province:
#         await context.bot.send_message(user_id, "❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
#         return

#     province_data = load_province_data(country, province)
#     if not province_data:
#         from province_handler import create_new_province
#         province_data = create_new_province(country, province)

#     # کسر ثروت
#     province_data["wealth"] -= total_price

#     item_name = item["name"]
#     item_type = item.get("type", "").lower()

#     # تعریف لیست معدن‌ها
#     mine_keys = [
#         "Stone mine", "Tin mine", "Iron mine", "Coal mine",
#         "Copper mine", "Silver mine", "Golden mine", "Diamond mine"
#     ]
    
#     # if item_type == "army":
#     #     base_count = item.get("count", 1)  # تعداد پایه سرباز در هر خرید
#     #     total_units = base_count * quantity  # مجموع سربازها
#     #     if "army" not in province_data:
#     #         province_data["army"] = {}
#     #     province_data["army"][item_name] = province_data["army"].get(item_name, 0) + total_units
#     #     province_data["total_army"] = province_data.get("total_army", 0) + total_units


#     # elif item_type == "weapon":
#     #     if "weapons" not in province_data:
#     #         province_data["weapons"] = []
#     #     province_data["weapons"].extend([item_name] * quantity)

#     # elif item_type == "castle":
#     #     if "castle" not in province_data:
#     #         province_data["castle"] = []
#     #     province_data["castle"].extend([item_name] * quantity)

#     # elif item_type == "structure":
#     #     if "structures" not in province_data:
#     #         province_data["structures"] = []
#     #     province_data["structures"].extend([item_name] * quantity)


#     if item_type == "army":
#         base_count = item.get("count", 1)  # تعداد پایه سرباز در هر خرید
#         total_units = base_count * quantity  # مجموع سربازها
#         if "army" not in province_data:
#             province_data["army"] = {}
#         province_data["army"][item_name] = province_data["army"].get(item_name, 0) + total_units
#         province_data["total_army"] = province_data.get("total_army", 0) + total_units
    
#     elif item_type == "weapon":
#         if "weapons" not in province_data:
#             province_data["weapons"] = {}
#         province_data["weapons"][item_name] = province_data["weapons"].get(item_name, 0) + quantity
    
#     elif item_type == "castle":
#         if "castle" not in province_data:
#             province_data["castle"] = {}
#         province_data["castle"][item_name] = province_data["castle"].get(item_name, 0) + quantity
    
#     elif item_type == "structure":
#         if "structures" not in province_data:
#             province_data["structures"] = {}
#         province_data["structures"][item_name] = province_data["structures"].get(item_name, 0) + quantity

#     # elif item_type == "econstructure":
#     #     if "mines" not in province_data:
#     #         # باید mines وجود داشته باشه ولی اگر نبود، می‌سازیم
#     #         province_data["mines"] = {key:0 for key in mine_keys}

#     #     if item_name in mine_keys:
#     #         # اگر معدن بود فقط مقدار اضافه میشه
#     #         province_data["mines"][item_name] = province_data["mines"].get(item_name, 0) + quantity
#     #     else:
#     #         # سازه اقتصادی
#     #         if "economic_structures" not in province_data:
#     #             province_data["economic_structures"] = {}

#     #         econ_structs = province_data["economic_structures"]

#     #         if item_name in econ_structs:
#     #             econ_structs[item_name]["count"] += quantity
#     #         else:
#     #             # ساخت سازه اقتصادی جدید
#     #             # استخراج product و weekly_output از description
#     #             description = item.get("description", "")
#     #             product = ""
#     #             weekly_output = 0
#     #             import re
#     #             try:
#     #                 parts = description.split('-')
#     #                 product = parts[0].strip()
#     #                 weekly_part = parts[1].strip() if len(parts) > 1 else ""
#     #                 match = re.search(r'(\d+)', weekly_part)
#     #                 if match:
#     #                     weekly_output = int(match.group(1))
#     #             except Exception:
#     #                 pass

#     #             econ_structs[item_name] = {
#     #                 "count": quantity,
#     #                 "product": product,
#     #                 "weekly_output": weekly_output
#     #             }
    
#     # بارگذاری دیکشنری مرکزی سازه‌ها
    
#     elif item_type == "econstructure":
#         if "economic_structures" not in province_data:
#             province_data["economic_structures"] = {}
    
#         econ_structs = province_data["economic_structures"]
    
#         if item_name in econ_structs:
#             # اگر قبلاً موجود بود، فقط count افزایش پیدا کنه
#             econ_structs[item_name]["count"] += quantity
#         else:
#             # اگر توی استان نبود، از فایل مرکزی بگیر
#             struct_info = all_econ_structs.get(item_name, {})
#             product = struct_info.get("product", "")
#             weekly_output = struct_info.get("weekly_output", 0)
    
#             econ_structs[item_name] = {
#                 "count": quantity,
#                 "product": product,
#                 "weekly_output": weekly_output
#             }

#     else:  # misc
#         if "misc" not in province_data:
#             province_data["misc"] = {}
#         province_data["misc"][item_name] = province_data["misc"].get(item_name, 0) + quantity

#     # ذخیره اطلاعات
#     save_province_data(country, province, province_data)

#     # حذف داده‌های خرید موقت
#     for key in ["purchase_item", "purchase_quantity", "total_price", "total_materials", "step", "flow_type"]:
#         context.user_data[user_id].pop(key, None)

#     text = f"✅ خرید با موفقیت انجام شد!\n\n"
#     text += f"📦 {item_name} × {quantity:,} به استان شما اضافه شد.\n"
#     text += f"💰 طلای باقی‌مانده: {province_data['wealth']:,} طلا"

#     keyboard = [
#         [InlineKeyboardButton("🏠 نمایش استان", callback_data="country_overview")],
#         [InlineKeyboardButton("🛒 ادامه خرید", callback_data="open_shop_menu")]
#     ]

#     await context.bot.send_message(
#         chat_id=query.message.chat_id,
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )




# async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     with open("economic_structures.json", "r", encoding="utf-8") as f:
#         all_econ_structs = json.load(f)

#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     item = user_data.get("purchase_item")
#     quantity = user_data.get("purchase_quantity", 1)
#     total_price = user_data.get("total_price", 0)
#     total_materials = user_data.get("total_materials", {})

#     if not item:
#         await context.bot.send_message(user_id, "❌ خطا در خرید.", reply_markup=back_and_home_buttons())
#         return

#     country = user_data.get("country")
#     province = user_data.get("province")

#     if not country or not province:
#         await context.bot.send_message(user_id, "❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
#         return

#     province_data = load_province_data(country, province)
#     if not province_data:
#         from province_handler import create_new_province
#         province_data = create_new_province(country, province)

#     # کسر ثروت
#     province_data["wealth"] -= total_price

#     item_name = item["name"]
#     item_type = item.get("type", "").lower()

#     # تعریف لیست معدن‌ها
#     mine_keys = [
#         "Stone mine", "Tin mine", "Iron mine", "Coal mine",
#         "Copper mine", "Silver mine", "Golden mine", "Diamond mine"
#     ]

#     if item_type == "army":
#         base_count = item.get("count", 1)
#         total_units = base_count * quantity
#         if "army" not in province_data:
#             province_data["army"] = {}
#         province_data["army"][item_name] = province_data["army"].get(item_name, 0) + total_units
#         province_data["total_army"] = province_data.get("total_army", 0) + total_units

#     elif item_type == "weapon":
#         if "weapons" not in province_data:
#             province_data["weapons"] = {}
#         province_data["weapons"][item_name] = province_data["weapons"].get(item_name, 0) + quantity

#     elif item_type == "castle":
#         if "castle" not in province_data:
#             province_data["castle"] = {}
#         province_data["castle"][item_name] = province_data["castle"].get(item_name, 0) + quantity

#     elif item_type == "structure":
#         if "structures" not in province_data:
#             province_data["structures"] = {}
#         province_data["structures"][item_name] = province_data["structures"].get(item_name, 0) + quantity

#     elif item_type == "econstructure":
#         if "economic_structures" not in province_data:
#             province_data["economic_structures"] = {}

#         econ_structs = province_data["economic_structures"]

#         if item_name in econ_structs:
#             # اگه قبلاً وجود داره (حتی با count=0) فقط count رو زیاد کن
#             econ_structs[item_name]["count"] = econ_structs[item_name].get("count", 0) + quantity
#         else:
#             # فقط اگر اصلاً وجود نداره، بسازش
#             struct_info = all_econ_structs.get(item_name, {})
#             econ_structs[item_name] = {
#                 "count": quantity,
#                 "product": struct_info.get("product", ""),
#                 "weekly_output": struct_info.get("weekly_output", 0)
#             }

#     else:  # misc
#         if "misc" not in province_data:
#             province_data["misc"] = {}
#         province_data["misc"][item_name] = province_data["misc"].get(item_name, 0) + quantity

#     # ذخیره اطلاعات
#     save_province_data(country, province, province_data)

#     # حذف داده‌های خرید موقت
#     for key in ["purchase_item", "purchase_quantity", "total_price", "total_materials", "step", "flow_type"]:
#         context.user_data[user_id].pop(key, None)

#     text = f"✅ خرید با موفقیت انجام شد!\n\n"
#     text += f"📦 {item_name} × {quantity:,} به استان شما اضافه شد.\n"
#     text += f"💰 طلای باقی‌مانده: {province_data['wealth']:,} طلا"

#     keyboard = [
#         [InlineKeyboardButton("🏠 نمایش استان", callback_data="country_overview")],
#         [InlineKeyboardButton("🛒 ادامه خرید", callback_data="open_shop_menu")]
#     ]

#     await context.bot.send_message(
#         chat_id=query.message.chat_id,
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )


async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    with open("economic_structures.json", "r", encoding="utf-8") as f:
        all_econ_structs = json.load(f)

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    item = user_data.get("purchase_item")
    quantity = user_data.get("purchase_quantity", 1)
    total_price = user_data.get("total_price", 0)
    total_materials = user_data.get("total_materials", {})

    if not item:
        await context.bot.send_message(user_id, "❌ خطا در خرید.", reply_markup=back_and_home_buttons())
        return

    country = user_data.get("country")
    province = user_data.get("province")

    if not country or not province:
        await context.bot.send_message(user_id, "❌ اطلاعات استان یافت نشد.", reply_markup=back_and_home_buttons())
        return

    province_data = load_province_data(country, province)
    if not province_data:
        from province_handler import create_new_province
        province_data = create_new_province(country, province)

    # 🔻 کسر ثروت
    province_data["wealth"] -= total_price

    # 🔻 کسر متریال‌ها
    for mat, required_amount in total_materials.items():
        remaining = required_amount

        # مصرف از همه بخش‌ها
        sections = ["army", "castle", "structures", "weapons", "misc", "economic_items"]
        for section_name in sections:
            if remaining <= 0:
                break
            section = province_data.get(section_name, {})
            if mat in section and section[mat] > 0:
                available = section[mat]
                consume = min(available, remaining)
                section[mat] -= consume
                remaining -= consume

        # اگر هنوز باقی موند از economic_items کم کن
        if remaining > 0:
            econ_items = province_data.setdefault("economic_items", {})
            if mat in econ_items and econ_items[mat] > 0:
                available = econ_items[mat]
                consume = min(available, remaining)
                econ_items[mat] -= consume
                remaining -= consume

    item_name = item["name"]
    item_type = item.get("type", "").lower()

    # 🔻 اضافه کردن آیتم به استان
    if item_type == "army":
        base_count = item.get("count", 1)
        total_units = base_count * quantity
        province_data.setdefault("army", {})
        province_data["army"][item_name] = province_data["army"].get(item_name, 0) + total_units
        province_data["total_army"] = province_data.get("total_army", 0) + total_units

    elif item_type == "weapon":
        province_data.setdefault("weapons", {})
        province_data["weapons"][item_name] = province_data["weapons"].get(item_name, 0) + quantity

    elif item_type == "castle":
        province_data.setdefault("castle", {})
        province_data["castle"][item_name] = province_data["castle"].get(item_name, 0) + quantity

    elif item_type == "structure":
        province_data.setdefault("structures", {})
        province_data["structures"][item_name] = province_data["structures"].get(item_name, 0) + quantity

    elif item_type == "econstructure":
        province_data.setdefault("economic_structures", {})
        econ_structs = province_data["economic_structures"]

        if item_name in econ_structs:
            econ_structs[item_name]["count"] = econ_structs[item_name].get("count", 0) + quantity
        else:
            struct_info = all_econ_structs.get(item_name, {})
            econ_structs[item_name] = {
                "count": quantity,
                "product": struct_info.get("product", ""),
                "weekly_output": struct_info.get("weekly_output", 0)
            }

    else:  # misc
        province_data.setdefault("misc", {})
        province_data["misc"][item_name] = province_data["misc"].get(item_name, 0) + quantity

    # 🔻 ذخیره اطلاعات
    save_province_data(country, province, province_data)

    # 🔻 حذف داده‌های موقت خرید
    for key in ["purchase_item", "purchase_quantity", "total_price", "total_materials", "step", "flow_type"]:
        context.user_data[user_id].pop(key, None)

    text = f"✅ خرید با موفقیت انجام شد!\n\n"
    text += f"📦 {item_name} × {quantity:,} به استان شما اضافه شد.\n"
    text += f"💰 طلای باقی‌مانده: {province_data['wealth']:,} طلا"

    keyboard = [
        [InlineKeyboardButton("🏠 نمایش استان", callback_data="country_overview")],
        [InlineKeyboardButton("🛒 ادامه خرید", callback_data="open_shop_menu")]
    ]

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )





# Legacy function for compatibility
async def fetch_channel_items(context: ContextTypes.DEFAULT_TYPE):
    """Fetch shop items from local JSON file (replaces channel reading)"""
    return load_shop_items()

async def handle_shop_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shop item purchase"""
    query = update.callback_query
    await query.answer()

    try:
        # Extract item index from callback data
        item_index = int(query.data.replace("shop_buy_", ""))

        user_id = query.from_user.id
        user_data = context.user_data.get(user_id, {})
        shop_items = user_data.get("shop_items", [])

        if 0 <= item_index < len(shop_items):
            item = shop_items[item_index]

            # Here you would implement the actual purchase logic
            # For now, just show a confirmation message
            await context.bot.send_message(
                f"✅ خرید موفقیت‌آمیز!\n\n📦 آیتم: {item.get('name', 'نامشخص')}\n💰 قیمت: {item.get('price', 0):,} طلا",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت به فروشگاه", callback_data="open_shop_menu")
                ]])
            )
        else:
            await context.bot.send_message(
                "❌ آیتم یافت نشد.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")
                ]])
            )
    except Exception as e:
        logger.error(f"Error in shop buy: {e}")
        await context.bot.send_message(
            "❌ خطا در خرید آیتم",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data="open_shop_menu")
            ]])
        )

async def show_shop_page(query, context, user_id, page):
    """Show shop items with navigation"""
    user_data = context.user_data.get(user_id, {})
    items = user_data.get("shop_items", [])

    if not items:
        await context.bot.send_message(
            "📭 هیچ آیتمی در فروشگاه یافت نشد.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")
            ]])
        )
        return

    total_pages = len(items)
    page = max(0, min(page, total_pages - 1))
    current_item = items[page]

    # Format item display
    text = f"🛒 فروشگاه - آیتم {page + 1} از {total_pages}\n\n"
    text += f"📦 {current_item['name']}\n\n"
    text += f"🏷 نوع: {current_item['type']}\n"
    # text += f"🌍 کشور: {current_item['country']}\n"
    countries = current_item.get('countries')
    country = current_item.get('country')
    
    if countries and isinstance(countries, list) and len(countries) > 0:
        countries_str = ', '.join(countries)
    elif country:
        countries_str = country
    else:
        countries_str = 'نامشخص'
    
    text += f"🌍 کشورها: {countries_str}\n"

    text += f"💰 قیمت: {current_item['price']:,} طلا\n"

    if current_item.get('materials'):
        text += "\n🔧 مواد مورد نیاز:\n"
        for material, amount in current_item['materials'].items():
            text += f"   • {material}: {amount:,}\n"

    if current_item.get('description'):
        text += f"\n📝 توضیحات:\n{current_item['description']}\n"

    if current_item.get('hashtags'):
        text += f"\n🏷️ برچسب‌ها: {' '.join(current_item['hashtags'])}\n"

    text += f"\n👤 فروشنده: {current_item.get('owner', 'نامشخص')}"

    # Navigation buttons
    nav_buttons = []
    if total_pages > 1:
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"shop_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"shop_page_{page+1}"))

    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Buy button
    keyboard.append([InlineKeyboardButton("🛒 خرید", callback_data=f"shop_buy_{page}")])

    # Back button - use back_to_previous for proper navigation
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_previous")])

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
                    parse_mode='Markdown'
                )
            except Exception as photo_error:
                logger.error(f"Error sending photo: {photo_error}")
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
        else:
            await context.bot.send_message(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error displaying item: {e}")
        try:
            await context.bot.send_message(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
