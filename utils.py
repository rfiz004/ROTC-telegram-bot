
from config import SKILLS_PER_PAGE
import re

def chunk_list(lst, size):
    """تقسیم لیست به بخش‌های کوچکتر"""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def format_bio_text(bio_data):
    """Format bio data into display text"""
    return (
        f"── ⃟ ⃟─⊳𝗕𝗶𝗼𝗴𝗿𝗮𝗽𝗵𝘆 ──╰𝗟𝗲𝘃𝗲𝗹 /\n"
        f"─ 𝗡𝗮𝗺𝗲 ─⊳ {bio_data['name']}\n"
        f"─ 𝗡𝗶𝗰𝗸𝗻𝗮𝗺𝗲 ─⊳ {bio_data['nickname']}\n"
        f"─ 𝗔𝗴𝗲 ─⊳ {bio_data['age']}\n"
        f"─ 𝗝𝗼𝗯 ─⊳ {bio_data['job']}\n"
        f"─ Countries ─⊳ {bio_data['country']}\n"
        f"─ Skills ─⊳ \n{', '.join(bio_data.get('skills', []))}\n"
        f"─ Level ─⊳ {bio_data['level']}\n"
        f"─ 𝗔𝗽𝗽𝗲𝗮𝗿𝗮𝗻𝗰𝗲 ─⊳ \n{bio_data['appearance']}\n"
        f"─ 𝗛𝗶𝘀𝘁𝗼𝗿𝘆 ─⊳ \n{bio_data['history']}\n"
        f"─ 𝗜𝗗 ─⊳ {bio_data['id_number']} | {bio_data['user_id_tag']}\n───────────  ⃟ ⃟─⊳ \n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
    )

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
    # Remove @ if user included it
    if username.startswith('@'):
        username = username[1:]
    
    # Check format
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$', username):
        return False, "❌ آیدی معتبر نیست. باید با حرف شروع بشه و بین 5 تا 32 کاراکتر باشه."
    
    return True, f"@{username}"
