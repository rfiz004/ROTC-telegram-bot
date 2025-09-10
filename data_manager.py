# import json
# import logging
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)

# # Initialize data structures
# jobs_by_country = {}
# skills_config = {"normal": [], "special": []}
# country_group_ids = {}
import json
import os
from telegram import Update
from telegram.ext import ContextTypes
import datetime
from datetime import datetime, timedelta
import base64
import requests
from config import BIOS_FILE, DATA_FILE, GITHUB_REPO, GITHUB_TOKEN, GITHUB_BRANCH, RESERVATION_FILE
import logging

logger = logging.getLogger(__name__)

ECONOMIC_PATH = "EconomicItems" 

async def handle_grain_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message = update.message.text.strip()
    allowed_grains = ["گوشت", "گندم", "ماهی", "مرغ", "میوه"]

    # جدا کردن اولویت‌ها
    priorities = [item.strip() for item in message.split("،") if item.strip() in allowed_grains]

    if not priorities:
        await update.message.reply_text("⛔ اولویت واردشده معتبر نیست. فقط از میان موارد گفته‌شده انتخاب کن.")
        return

    # دریافت استان انتخاب‌شده از user_data (باید قبلاً تنظیم شده باشه)
    province = context.user_data.get(user_id, {}).get("selected_province")
    if not province:
        await update.message.reply_text("⛔ ابتدا استان را انتخاب کن.")
        return

    province = province.strip().replace(" ", "_")
    file_path = os.path.join(ECONOMIC_PATH, f"{province}.json")


    if not os.path.exists(file_path):
        await update.message.reply_text("⛔ فایل اقتصادی استان پیدا نشد.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # بروزرسانی اولویت
    data["grain_priority"] = priorities

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("✅ اولویت غلات با موفقیت ذخیره شد.")
    context.user_data[user_id]["step"] = None
    return True

# async def handle_grain_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id
#     message = update.message.text.strip()

#     # پارس ورودی
#     parts = [item.strip() for item in message.split("،") if "=" in item]
#     grains = {}

#     for part in parts:
#         name, val = part.split("=")
#         name = name.strip()
#         try:
#             val = int(val.strip())
#         except ValueError:
#             continue

#         if val < 0 or val % 50 != 0:
#             continue

#         grains[name] = val

#     if not grains:
#         await update.message.reply_text("⛔ فرمت یا مقادیر واردشده معتبر نیستند.")
#         return

#     # province = context.user_data.get(user_id, {}).get("selected_province")
#     user_data = context.user_data.get(user_id, {})
#     province = user_data.get("selected_province")
#     province = province.strip().replace(" ", "_")

#     if not province:
#         await update.message.reply_text("⛔ ابتدا استان را انتخاب کن.")
#         return
        
#     print(f"Province after clean-up: '{province}'")
#     file_path = os.path.join(ECONOMIC_PATH, f"{province}.json")
#     print(f"Looking for file: '{file_path}'")

#     if not os.path.exists(file_path):
#         await update.message.reply_text("⛔ فایل اقتصادی استان پیدا نشد.")
#         return

#     with open(file_path, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     # بررسی اینکه فقط غلات مجاز تنظیم می‌شن
#     allowed = data.get("grain_priority", [])
#     invalid = [g for g in grains if g not in allowed]

#     if invalid:
#         await update.message.reply_text(f"⛔ نمی‌تونی برای این غلات درصد تنظیم کنی: {', '.join(invalid)}")
#         return

#     # ذخیره درصد
#     data["grains"] = grains

#     with open(file_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

#     await update.message.reply_text("✅ درصد مصرف غلات با موفقیت ذخیره شد.")
#     context.user_data[user_id]["step"] = None
#     return True


async def handle_grain_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    message = update.message.text.strip()

    # تلاش برای تبدیل به عدد
    try:
        val = int(message)
    except ValueError:
        await update.message.reply_text("⛔ لطفاً فقط یک عدد وارد کن (مضرب 50).")
        return

    # بررسی عدد
    if val < 0 or val % 50 != 0:
        await update.message.reply_text("⛔ عدد باید مضرب 50 و بدون مقدار منفی باشه.")
        return

    # گرفتن استان انتخاب‌شده
    user_data = context.user_data.get(user_id, {})
    province = user_data.get("selected_province")
    if not province:
        await update.message.reply_text("⛔ ابتدا استان را انتخاب کن.")
        return

    province = province.strip().replace(" ", "_")
    file_path = os.path.join(ECONOMIC_PATH, f"{province}.json")

    if not os.path.exists(file_path):
        await update.message.reply_text("⛔ فایل اقتصادی استان پیدا نشد.")
        return

    # بارگذاری و ذخیره درصد
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["grain_consumption"] = val  # 🔹 حالا فقط یک عدد کلی ذخیره می‌کنیم

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await update.message.reply_text("✅ درصد کلی مصرف غلات با موفقیت ذخیره شد.")
    context.user_data[user_id]["step"] = None
    return True


def load_data_file(file_path="data.json"):
    """Consolidated function to load data from JSON file"""
    global jobs_by_country, skills_config
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if file_path == "data.json":
            jobs_by_country = data.get("jobs_by_country", {})
            skills_config = data.get("skills_config", {"normal": [], "special": []})
        return data
    except FileNotFoundError:
        logger.warning(f"{file_path} not found, using default values")
        return {"jobs_by_country": {}, "skills_config": {"normal": [], "special": []}}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {"jobs_by_country": {}, "skills_config": {"normal": [], "special": []}}

def save_data_file(data, file_path="data.json"):
    """Consolidated function to save data to JSON file"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False

# # Maintain backward compatibility
# def load_data():
#     """Load main data file - backward compatibility"""
#     return load_data_file("data.json")

# def save_data(data, file_path="data.json"):
#     """Save data - backward compatibility"""
#     return save_data_file(data, file_path)


# def load_bios():
#     """Load bios from JSON file"""
#     try:
#         with open("bios.json", "r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return []
#     except Exception as e:
#         logger.error(f"Error loading bios: {e}")
#         return []

# def save_bios(bios):
#     """Save bios to JSON file"""
#     try:
#         with open("bios.json", "w", encoding="utf-8") as f:
#             json.dump(bios, f, ensure_ascii=False, indent=2)
#         return True
#     except Exception as e:
#         logger.error(f"Error saving bios: {e}")
#         return False

# def remove_bio_from_storage(user_id):
#     """Remove bio from storage"""
#     try:
#         bios = load_bios()
#         bios = [bio for bio in bios if isinstance(bio, dict) and bio.get("user_id") != user_id]
#         save_bios(bios)
#         return True
#     except Exception as e:
#         logger.error(f"Error removing bio: {e}")
#         return False

# def remove_used_hashtag(hashtag):
#     """Remove used hashtag (placeholder)"""
#     # This would remove hashtag from used hashtags list
#     pass

# def clear_expired_reservations(jobs_data):
#     """Clear expired job reservations"""
#     try:
#         cleared_count = 0
#         current_time = datetime.now()

#         for country, jobs in jobs_data.items():
#             for job in jobs:
#                 if "reserved_until" in job:
#                     reserved_until = datetime.fromisoformat(job["reserved_until"])
#                     if current_time > reserved_until:
#                         job.pop("reserved_until", None)
#                         job.pop("reserved_by", None)
#                         job["count"] = job.get("count", 0) + 1
#                         cleared_count += 1

#         if cleared_count > 0:
#             save_data({"jobs_by_country": jobs_data, "skills_config": skills_config})

#         return cleared_count
#     except Exception as e:
#         logger.error(f"Error clearing reservations: {e}")
#         return 0

# # Load initial data
# load_data()





def get_used_hashtags():
    bios = load_bios()
    return bios.get("used_hashtags", [])

def add_used_hashtag(tag):
    bios = load_bios()
    used = bios.get("used_hashtags", [])
    if tag not in used:
        used.append(tag)
    bios["used_hashtags"] = used
    save_bios(bios)

def remove_used_hashtag(tag):
    bios = load_bios()
    used = bios.get("used_hashtags", [])
    if tag in used:
        used.remove(tag)
    bios["used_hashtags"] = used
    save_bios(bios)

def read_bios():
    if not os.path.exists("bios.json"):
        return {}
    with open("bios.json", "r", encoding="utf-8") as f:
        return json.load(f)

def write_bios(data):
    with open("bios.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_bios():
    """Load bios from JSON file with proper error handling"""
    try:
        if os.path.exists(BIOS_FILE):
            with open(BIOS_FILE, 'r', encoding='utf-8') as f:
                bios = json.load(f)
                if not isinstance(bios, dict):
                    logger.warning(f"Invalid bios structure in {BIOS_FILE}")
                    return {}
                return bios
        else:
            logger.info(f"📁 {BIOS_FILE} not found, returning empty dict")
            return {}
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.error(f"⚠️ Error reading {BIOS_FILE}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading bios: {e}")
        return {}

def save_bios(bios):
    """Save bios to JSON file with proper error handling"""
    try:
        # Create backup first
        if os.path.exists(BIOS_FILE):
            backup_file = f"{BIOS_FILE}.backup"
            try:
                with open(BIOS_FILE, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except:
                pass

        # Save new bios
        with open(BIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(bios, f, ensure_ascii=False, indent=2)
        logger.info("Bios saved successfully")
    except Exception as e:
        logger.error(f"❌ Error saving bios: {e}")
        raise

# def add_bio_to_storage(user_id, bio_data):
#     bios = load_bios()
#     if "bios" not in bios:
#         bios["bios"] = {}
#     bios["bios"][str(user_id)] = bio_data
#     save_bios(bios)
#     if GITHUB_TOKEN and GITHUB_REPO:
#         upload_to_github(BIOS_FILE, json.dumps(bios, ensure_ascii=False, indent=2))

def add_bio_to_storage(user_id, bio_data):
    bios = load_bios()
    uid = str(user_id)

    bio_data["timestamp"] = datetime.now().isoformat()

    # حفظ لیست هشتگ‌ها
    existing_hashtags = bios.get("used_hashtags", [])
    if "bios" not in bios:
        bios["bios"] = {}
    if "used_hashtags" not in bios:
        bios["used_hashtags"] = []
    bios["bios"][uid] = bio_data
    bios["used_hashtags"] = existing_hashtags

    # حذف بیوهای قدیمی
    cutoff = datetime.now() - timedelta(days=7)
    bios["bios"] = {
        k: v for k, v in bios["bios"].items()
        if "timestamp" in v and datetime.fromisoformat(v["timestamp"]) > cutoff
    }

    tag = bio_data.get("user_id_tag")
    if tag and tag not in bios["used_hashtags"]:
        bios["used_hashtags"].append(tag)

    save_bios(bios)

def remove_bio_from_storage(user_id):
    bios = load_bios()
    uid = str(user_id)
    if "bios" in bios and uid in bios["bios"]:
        tag = bios["bios"][uid].get("user_id_tag")
        used = bios.get("used_hashtags", [])
        if tag and tag in used:
            used.remove(tag)
            bios["used_hashtags"] = used
        del bios["bios"][uid]
        save_bios(bios)
        save_bios(bios)

# لود دیتا
def load_data():
    """Load data from JSON file with proper error handling"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate data structure
                if not isinstance(data, dict):
                    logger.warning(f"Invalid data structure in {DATA_FILE}, creating new")
                    return create_default_data()
                return data
        else:
            logger.info(f"📁 {DATA_FILE} not found, creating new structure")
            return create_default_data()
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.error(f"⚠️ Error reading {DATA_FILE}: {e}, creating new structure")
        return create_default_data()
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        return create_default_data()

def save_data_with_merge(new_data):
    """Save data with merging - specialized function"""
    # مرحله ۱: خواندن محتوای فعلی
    existing_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}

    # مرحله ۲: ترکیب با داده‌های جدید
    merged_data = existing_data.copy()
    merged_data.update(new_data)

    # مرحله ۳: ذخیره در فایل
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    # مرحله ۴: آپلود در گیت‌هاب
    if GITHUB_TOKEN and GITHUB_REPO:
        upload_to_github(DATA_FILE, json.dumps(merged_data, ensure_ascii=False, indent=2))


def load_job_reservations():
    if not os.path.exists(RESERVATION_FILE):
        return {}
    try:
        with open(RESERVATION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_job_reservations(data):
    with open(RESERVATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if GITHUB_TOKEN and GITHUB_REPO:
        upload_to_github(RESERVATION_FILE, json.dumps(data, ensure_ascii=False, indent=2))


def clear_expired_reservations(jobs_by_country):
    reservations = load_job_reservations()
    bios = load_bios()
    now = datetime.utcnow()
    expired_users = []

    for user_id, info in reservations.items():
        reserved_at = datetime.fromisoformat(info["reserved_at"])

        # Only clear if reservation is expired AND user doesn't have a pending bio
        if now - reserved_at > timedelta(minutes=30) and user_id not in bios.get("bios", {}):
            country = info["country"]
            job_name = info["job"]
            job_list = jobs_by_country.get(country, [])

            for job in job_list:
                if job["name"] == job_name:
                    job["count"] += 1
                    break

            expired_users.append(user_id)

    for user_id in expired_users:
        del reservations[user_id]

    if expired_users:
        save_job_reservations(reservations)
        save_data({"jobs_by_country": jobs_by_country, "skills_config": skills_config})

    return len(expired_users)

def upload_to_github(filename, content):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print(f"⚠️ GitHub config missing, skipping upload for {filename}")
        return

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        content_encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None

        data = {
            "message": f"update {filename}",
            "content": content_encoded,
            "branch": GITHUB_BRANCH,
        }
        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            print(f"✅ {filename} در گیت‌هاب ذخیره شد.")
        else:
            print(f"❌ خطا در ذخیره {filename}: {response.text}")
    except Exception as e:
        print(f"❌ خطا در آپلود {filename}: {e}")

# Initialize data with safe fallbacks
data = load_data()
jobs_by_country = data.get("jobs_by_country", {})
skills_config = data.get("skills_config", {
    "normal": [],
    "special": [],
    "required_skills_for": {},
    "extended_limit_if_has": {}
})
country_group_ids = data.get("country_group_ids", {})
import json
import os
from datetime import datetime

# Default data structures
jobs_by_country = {
    "Aldemar": [],
    "Alpyr": [],
    "Walden": [],
    "Northwood": [],
    "Santos": [],
    "Imperial": [],
    "Azure": [],
    "Hikada": [],
    "Alestria": []
}

skills_config = {
    "normal": ["مهارت عادی 1", "مهارت عادی 2", "مهارت عادی 3"],
    "special": ["مهارت خاص 1", "مهارت خاص 2"],
    "extended_limit_if_has": {"مدیریت امور داخلی": 5},
    "required_skills_for": {}
}

def save_data(filename, data):
    """Save data to JSON file with error handling"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        return False

def load_passwords():
    """Load passwords data"""
    return load_data("passwords.json")

# Function removed - using consolidated load_data_file function

def load_bios():
    """Load bios from JSON file with proper error handling"""
    try:
        if os.path.exists("bios.json"):
            with open("bios.json", 'r', encoding='utf-8') as f:
                bios = json.load(f)
                if not isinstance(bios, dict):
                    logger.warning(f"Invalid bios structure in bios.json")
                    return {"bios": {}}
                return bios
        else:
            logger.info(f"📁 bios.json not found, returning empty dict")
            return {"bios": {}}
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.error(f"⚠️ Error reading bios.json: {e}")
        return {"bios": {}}
    except Exception as e:
        logger.error(f"Unexpected error loading bios: {e}")
        return {"bios": {}}

def save_bios(bios_data):
    """Save bios to JSON file with proper error handling"""
    try:
        # Create backup first
        if os.path.exists("bios.json"):
            backup_file = f"bios.json.backup"
            try:
                with open("bios.json", 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            except:
                pass

        # Save new bios
        with open("bios.json", "w", encoding="utf-8") as f:
            json.dump(bios_data, f, ensure_ascii=False, indent=2)
        logger.info("Bios saved successfully")
    except Exception as e:
        logger.error(f"❌ Error saving bios: {e}")
        return False

def load_passwords():
    """Load passwords from JSON file"""
    if not os.path.exists("passwords.json"):
        return {"passwords": {}}

    try:
        with open("passwords.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ خطا در بارگذاری رمزها: {e}")
        return {"passwords": {}}

def add_bio_to_storage(user_id, bio_data):
    """Add bio to storage"""
    bios = load_bios()
    bios["bios"][str(user_id)] = bio_data
    save_bios(bios)

def remove_bio_from_storage(user_id):
    """Remove bio from storage"""
    bios = load_bios()
    if str(user_id) in bios["bios"]:
        del bios["bios"][str(user_id)]
        save_bios(bios)

def get_used_hashtags():
    """Get list of used hashtags"""
    # This could be stored in a separate file or in the bios data
    bios = load_bios()
    used_tags = []
    for bio in bios.get("bios", {}).values():
        if "user_id_tag" in bio:
            used_tags.append(bio["user_id_tag"])
    return used_tags

def add_used_hashtag(hashtag):
    """Add hashtag to used list (this is handled by bio storage)"""
    pass

def remove_used_hashtag(hashtag):
    """Remove hashtag from used list (this is handled by bio removal)"""
    pass

def load_job_reservations():
    """Load job reservations from JSON file"""
    if not os.path.exists("job_reservations.json"):
        return {}

    try:
        with open("job_reservations.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ خطا در بارگذاری رزروها: {e}")
        return {}

def save_job_reservations(reservations):
    """Save job reservations to JSON file"""
    try:
        with open("job_reservations.json", "w", encoding="utf-8") as f:
            json.dump(reservations, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره رزروها: {e}")
        return False

def clear_expired_reservations(jobs_by_country):
    """Clear expired job reservations"""
    reservations = load_job_reservations()
    current_time = datetime.utcnow()
    expired_count = 0

    expired_users = []
    for user_id, reservation in reservations.items():
        reserved_at = datetime.fromisoformat(reservation["reserved_at"])
        if (current_time - reserved_at).total_seconds() > 1800:  # 30 minutes
            expired_users.append(user_id)

            # Return job to available pool
            country = reservation["country"]
            job = reservation["job"]
            job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job), None)
            if job_data:
                job_data["count"] += 1
                expired_count += 1

    # Remove expired reservations
    for user_id in expired_users:
        del reservations[user_id]

    if expired_users:
        save_job_reservations(reservations)
        # save_data({"jobs_by_country": jobs_by_country, "skills_config": skills_config})
        save_data("data.json", {"jobs_by_country": jobs_by_country, "skills_config": skills_config})


    return expired_count

# Initialize data with safe loading
try:
    data = load_data()
    jobs_by_country = data.get("jobs_by_country", {})
    skills_config = data.get("skills_config", {
        "normal": ["تیراندازی با کمان", "شمشیرزنی", "سوارکاری", "مدیریت امور داخلی", "آهنگری"],
        "special": ["مخفی‌کاری", "قدرت بدنی بالا", "سرعت بالا"],
        "extended_limit_if_has": {"مدیریت امور داخلی": 5},
        "required_skills_for": {"ساخت دارو و سم": ["داروشناسی", "سم شناسی"]}
    })
    country_group_ids = data.get("country_group_ids", {
    "Alpyr": -1002639123059,
    "Aldemar": -1002758643989,
    "Imperial": -1002526473244,
    "Hikada": -1002725641455,
    "Walden": -1002814211271,
    "Northwood": -1002786852947,
    "Santos": -1002786128458,
    "Alestria": -1002633440186,
    "Azure": -1002805143456})
except Exception as e:
    print(f"❌ Error loading data: {e}")
    jobs_by_country = {}
    skills_config = {
        "normal": ["تیراندازی با کمان", "شمشیرزنی", "سوارکاری", "مدیریت امور داخلی", "آهنگری"],
        "special": ["مخفی‌کاری", "قدرت بدنی بالا", "سرعت بالا"],
        "extended_limit_if_has": {"مدیریت امور داخلی": 5},
        "required_skills_for": {"ساخت دارو و سم": ["داروشناسی", "سم شناسی"]}
    }
    country_group_ids = {
    "Alpyr": -1002639123059,
    "Aldemar": -1002758643989,
    "Imperial": -1002526473244,
    "Hikada": -1002725641455,
    "Walden": -1002814211271,
    "Northwood": -1002786852947,
    "Santos": -1002786128458,
    "Alestria": -1002633440186,
    "Azure": -1002805143456}
