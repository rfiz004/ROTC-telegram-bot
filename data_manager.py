
import json
import os
import datetime
from datetime import datetime, timedelta
import base64
import requests
from config import BIOS_FILE, DATA_FILE, GITHUB_REPO, GITHUB_TOKEN, GITHUB_BRANCH, RESERVATION_FILE


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
    if not os.path.exists(BIOS_FILE):
        return {"bios": {}, "used_hashtags": []}
    try:
        with open(BIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure proper structure
            if "bios" not in data:
                data["bios"] = {}
            if "used_hashtags" not in data:
                data["used_hashtags"] = []
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {"bios": {}, "used_hashtags": []}

def save_bios(bios):
    with open(BIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(bios, f, ensure_ascii=False, indent=2)

def add_bio_to_storage(user_id, bio_data):
    bios = load_bios()
    if "bios" not in bios:
        bios["bios"] = {}
    bios["bios"][str(user_id)] = bio_data
    save_bios(bios)
    if GITHUB_TOKEN and GITHUB_REPO:
        upload_to_github(BIOS_FILE, json.dumps(bios, ensure_ascii=False, indent=2))

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

def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "jobs_by_country": {},
            "skills_config": {
                "normal": [],
                "special": [],
                "required_skills_for": {},
                "extended_limit_if_has": {}
            }
        }
        save_data(default_data)
        return default_data
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Ensure all required keys exist with safe fallbacks
            if "jobs_by_country" not in data:
                data["jobs_by_country"] = {}
            if "skills_config" not in data:
                data["skills_config"] = {}
            if "normal" not in data["skills_config"]:
                data["skills_config"]["normal"] = []
            if "special" not in data["skills_config"]:
                data["skills_config"]["special"] = []
            if "required_skills_for" not in data["skills_config"]:
                data["skills_config"]["required_skills_for"] = {}
            if "extended_limit_if_has" not in data["skills_config"]:
                data["skills_config"]["extended_limit_if_has"] = {}
            
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        default_data = {
            "jobs_by_country": {},
            "skills_config": {
                "normal": [],
                "special": [],
                "required_skills_for": {},
                "extended_limit_if_has": {}
            }
        }
        save_data(default_data)
        return default_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if GITHUB_TOKEN and GITHUB_REPO:
        upload_to_github(DATA_FILE, json.dumps(data, ensure_ascii=False, indent=2))

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
