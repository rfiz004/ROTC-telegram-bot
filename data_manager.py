
import json
import os
import datetime
from datetime import datetime, timedelta, timezone
import base64
import requests
from config import BIOS_FILE, DATA_FILE, GITHUB_REPO, GITHUB_TOKEN, GITHUB_BRANCH

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
        return {}
    with open(BIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_bios(bios):
    with open(BIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(bios, f, ensure_ascii=False, indent=2)
    upload_to_github(BIOS_FILE, bios)


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
        return {"jobs_by_country": {}, "skills_list": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    upload_to_github(DATA_FILE, data)
    
def upload_to_github(filename, data_dict, commit_message=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # ✅ تبدیل به JSON در همینجا
    json_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
    content_encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": commit_message or f"update {filename}",
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


RESERVATION_FILE = "job_reservations.json"

def load_job_reservations():
    if not os.path.exists(RESERVATION_FILE):
        return {}
    with open(RESERVATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_job_reservations(data):
    with open(RESERVATION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    upload_to_github(RESERVATION_FILE, data)


    def clear_expired_reservations(jobs_by_country):
        reservations = load_job_reservations()
        now = datetime.now(timezone.utc)
        expired_users = []

        for user_id, info in reservations.items():
            reserved_at = datetime.fromisoformat(info["reserved_at"])
            if now - reserved_at > timedelta(minutes=30):
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
            save_data({"jobs_by_country": jobs_by_country})

# Initialize data
data = load_data()
jobs_by_country = data["jobs_by_country"]
skills_config = data["skills_config"]

