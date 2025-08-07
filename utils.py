from config import SKILLS_PER_PAGE
import re
import logging

logger = logging.getLogger(__name__)

def chunk_list(lst, size):
    """تقسیم لیست به بخش‌های کوچکتر"""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

# def format_bio_text(bio_data):
#     """Format bio data for display"""
#     try:
#         if not bio_data or not isinstance(bio_data, dict):
#             return "❌ اطلاعات بیوگرافی نامعتبر"

#         text = f"👤 **نام کاراکتر:** {bio_data.get('character_name', bio_data.get('name', 'نامشخص'))}\n"
#         text += f"🌍 **کشور:** {bio_data.get('country', 'نامشخص')}\n"
#         text += f"💼 **شغل:** {bio_data.get('job', 'نامشخص')}\n"

#         # Add province if available
#         if bio_data.get('province'):
#             text += f"📍 **استان:** {bio_data.get('province')}\n"

#         text += f"🏷️ **هشتگ:** {bio_data.get('hashtag', bio_data.get('user_id_tag', 'نامشخص'))}\n"
#         text += f"📱 **آیدی تلگرام:** {bio_data.get('telegram_id', bio_data.get('user_id', 'نامشخص'))}\n"

#         # Add skills if available
#         skills = bio_data.get('skills', [])
#         if skills:
#             if isinstance(skills, list):
#                 text += f"🎯 **مهارت‌ها:** {', '.join(skills)}\n"
#             else:
#                 text += f"🎯 **مهارت‌ها:** {skills}\n"

#         # Add description if available
#         description = bio_data.get('description', bio_data.get('bio', ''))
#         if description:
#             text += f"📝 **توضیحات:** {description}\n"

#         # Add timestamp if available
#         created_at = bio_data.get('created_at', bio_data.get('timestamp', ''))
#         if created_at:
#             text += f"📅 **تاریخ ثبت:** {created_at}\n"

#         return text
#     except Exception as e:
#         logger.error(f"Error formatting bio text: {e}")
#         return "❌ خطا در نمایش اطلاعات بیوگرافی"


def format_bio_text(bio_data):
    """Format bio data into styled display text"""

    try:
        if not bio_data or not isinstance(bio_data, dict):
            return "❌ اطلاعات بیوگرافی نامعتبر"

        name = bio_data.get('name', bio_data.get('character_name', 'نامشخص'))
        nickname = bio_data.get('nickname', 'نامشخص')
        age = bio_data.get('age', 'نامشخص')
        job = bio_data.get('job', 'نامشخص')
        country = bio_data.get('country', 'نامشخص')
        skills = bio_data.get('skills', [])
        level = bio_data.get('level', 'نامشخص')
        appearance = bio_data.get('appearance', 'نامشخص')
        history = bio_data.get('history', 'نامشخص')
        id_number = bio_data.get('id_number', 'نامشخص')
        user_id_tag = bio_data.get('user_id_tag', bio_data.get('hashtag', 'نامشخص'))

        if isinstance(skills, list):
            skills_text = ', '.join(skills) if skills else 'نامشخص'
        else:
            skills_text = skills or 'نامشخص'

        return (
            f"── ⃟ ⃟─⊳𝗕𝗶𝗼𝗴𝗿𝗮𝗽𝗵𝘆 ──╰𝗟𝗲𝘃𝗲𝗹 /\n"
            f"─ 𝗡𝗮𝗺𝗲 ─⊳ {name}\n"
            f"─ 𝗡𝗶𝗰𝗸𝗻𝗮𝗺𝗲 ─⊳ {nickname}\n"
            f"─ 𝗔𝗴𝗲 ─⊳ {age}\n"
            f"─ 𝗝𝗼𝗯 ─⊳ {job}\n"
            f"─ Countries ─⊳ {country}\n"
            f"─ Skills ─⊳ \n{skills_text}\n"
            f"─ Level ─⊳ {level}\n"
            f"─ 𝗔𝗽𝗽𝗲𝗮𝗿𝗮𝗻𝗰𝗲 ─⊳ \n{appearance}\n"
            f"─ 𝗛𝗶𝘀𝘁𝗼𝗿𝘆 ─⊳ \n{history}\n"
            f"─ 𝗜𝗗 ─⊳ {id_number} | {user_id_tag}\n"
            f"───────────  ⃟ ⃟─⊳ \n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
        )

    except Exception as e:
        # در صورت نیاز، این خط را فعال کنید
        # logger.error(f"Error formatting bio text: {e}")
        return "❌ خطا در نمایش اطلاعات بیوگرافی"


def calculate_skill_pages(skills_list):
    """Calculate total pages for skill pagination"""
    return (len(skills_list) + SKILLS_PER_PAGE - 1) // SKILLS_PER_PAGE

def get_page_skills(skills_list, page):
    """Get skills for a specific page"""
    start = page * SKILLS_PER_PAGE
    end = start + SKILLS_PER_PAGE
    return skills_list[start:end]

def validate_age(text):
    """Validate age input"""
    try:
        age = int(text)
        return 13 <= age <= 100
    except ValueError:
        return False

def validate_hashtag(hashtag, used_hashtags):
    """Validate hashtag format and uniqueness"""
    # Remove # if user included it
    if hashtag.startswith('#'):
        hashtag = hashtag[1:]

    # Check format (alphanumeric and underscores only, reasonable length)
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', hashtag):
        return False, "❌ هشتگ باید بین 3 تا 20 کاراکتر باشه و فقط شامل حروف انگلیسی، اعداد و _ باشه."

    # Check if already used
    full_hashtag = f"#{hashtag}"
    if full_hashtag in used_hashtags:
        return False, "❌ این هشتگ قبلاً استفاده شده. یکی دیگه انتخاب کن:"

    return True, full_hashtag

def validate_username(username):
    """Validate Telegram username format"""
    if not username:
        return False, "❌ نام کاربری نمی‌تواند خالی باشد."

    # Remove @ if present
    if username.startswith('@'):
        username = username[1:]

    # Must be 5–32 chars, only letters, digits, underscores, and start with a letter
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', username):
        return False, "❌ آیدی معتبر نیست. باید با حرف شروع بشه، بین 5 تا 32 کاراکتر باشه و فقط شامل حروف انگلیسی، اعداد و _ باشه."

    return True, f"@{username}"
        
import json
from datetime import datetime

def generate_unique_id():
    """Generate unique ID for bio submissions"""
    return str(int(datetime.now().timestamp() * 1000))

def validate_user_input(text, input_type="general"):
    """Validate user input based on type"""
    try:
        if not text or not text.strip():
            return False, "متن نمی‌تواند خالی باشد"

        text = text.strip()

        if input_type == "character_name":
            if len(text) < 2:
                return False, "نام کاراکتر باید حداقل ۲ حرف باشد"
            if len(text) > 50:
                return False, "نام کاراکتر نمی‌تواند بیش از ۵۰ حرف باشد"

        elif input_type == "password":
            if len(text) < 3:
                return False, "رمز عبور باید حداقل ۳ حرف باشد"

        elif input_type == "news_text":
            if len(text) < 10:
                return False, "متن اعلامیه باید حداقل ۱۰ حرف باشد"
            if len(text) > 2000:
                return False, "متن اعلامیه نمی‌تواند بیش از ۲۰۰۰ حرف باشد"

        return True, text
    except Exception as e:
        logger.error(f"Error validating input: {e}")
        return False, "خطا در اعتبارسنجی ورودی"



def safe_get_nested(data, keys, default=None):
    """Safely get nested dictionary values"""
    try:
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return default
        return data
    except Exception:
        return default

def format_number(number):
    """Format numbers with thousands separator"""
    try:
        if isinstance(number, (int, float)):
            return f"{number:,}"
        return str(number)
    except:
        return "0"

def clean_callback_data(data):
    """Clean and validate callback data"""
    try:
        if not data:
            return ""
        # Remove any potentially problematic characters
        cleaned = re.sub(r'[^\w\-_|]', '', str(data))
        return cleaned[:64]  # Telegram callback data limit
    except:
        return ""

def check_admin_access(user_data, required_role=None, required_country=None):
    """Check if user has required admin access - consolidated function"""
    try:
        if not user_data.get("admin_session") and not user_data.get("admin_access"):
            return False

        user_role = user_data.get("admin_role") or user_data.get("role")

        if required_role:
            if user_role == "master_admin":
                return True
            elif user_role == required_role:
                return True
            elif user_role == "multi_country_admin" and required_role in ["bio_admin", "shop_admin", "province_admin"]:
                return True

        if required_country:
            admin_countries = user_data.get("admin_countries", [])
            return required_country.lower() in [c.lower() for c in admin_countries]

        # If no specific requirements, just check if user has any admin role
        return bool(user_role)
    except Exception as e:
        logger.error(f"Error checking admin access: {e}")
        return False

def push_navigation_state(user_data, current_state):
    """Push current state to navigation history - consolidated function"""
    if "navigation_history" not in user_data:
        user_data["navigation_history"] = []
    # Don't push duplicate states
    if not user_data["navigation_history"] or user_data["navigation_history"][-1] != current_state:
        user_data["navigation_history"].append(current_state)
    # Keep only last 10 states to prevent memory issues
    if len(user_data["navigation_history"]) > 10:
        user_data["navigation_history"] = user_data["navigation_history"][-10:]

def pop_navigation_state(user_data):
    """Pop and return previous state from navigation history - consolidated function"""
    nav_history = user_data.get("navigation_history", [])
    if nav_history:
        return nav_history.pop()
    return None

def get_current_navigation_state(user_data):
    """Get current navigation state without popping - consolidated function"""
    nav_history = user_data.get("navigation_history", [])
    return nav_history[-1] if nav_history else None