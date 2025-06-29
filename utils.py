import json
from config import SKILLS_PER_PAGE

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
    return text.isdigit() and 10 <= int(text) <= 100

def validate_hashtag(text):
    """Validate hashtag format"""
    return text.startswith("#") and text[1:].isalnum()

def validate_username(text):
    """Validate username format"""
    import re
    return re.match(r"^@[\w\d_]{5,}$", text)

def save_used_hashtag(hashtag: str):
    hashtag = hashtag.lower()
    try:
        with open("bios.json", "r") as f:
            data = json.load(f)
    except:
        data = {}

    if "used_hashtags" not in data:
        data["used_hashtags"] = {}

    data["used_hashtags"][hashtag] = True

    with open("bios.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_hashtag_unique_permanent(hashtag: str) -> bool:
    hashtag = hashtag.lower()
    try:
        with open("bios.json", "r") as f:
            data = json.load(f)
        return hashtag not in data.get("used_hashtags", {})
    except:
        return True
