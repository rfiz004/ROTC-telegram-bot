
import json
import os
import datetime
from datetime import datetime, timedelta
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

from datetime import datetime, timedelta
from storage import load_bios, save_bios

def add_bio_to_storage(user_id, bio_data):
    data = load_bios()
    uid = str(user_id)

    # 1. افزودن timestamp به بیو
    bio_data["timestamp"] = datetime.now().isoformat()

    # 2. ذخیره در بخش bios
    if "bios" not in data:
        data["bios"] = {}

    data["bios"][uid] = bio_data

    # 3. ذخیره هشتگ در بخش used_hashtags
    hashtag = bio_data.get("user_id_tag")
    if hashtag:
        if "used_hashtags" not in data:
            data["used_hashtags"] = {}

        data["used_hashtags"][hashtag] = {
            "timestamp": datetime.now().isoformat()
        }

    # 4. پاک‌سازی بیوهای قدیمی‌تر از 7 روز
    cutoff = datetime.now() - timedelta(days=7)
    data["bios"] = {
        k: v for k, v in data["bios"].items()
        if "timestamp" in v and datetime.fromisoformat(v["timestamp"]) > cutoff
    }

    # 5. ذخیره نهایی
    save_bios(data)

    try:
        upload_to_github("bios.json", data, "Update bios & hashtags")
    except Exception as e:
        print("❌ خطا در آپلود فایل bios.json به گیت‌هاب:", e)


# def add_bio_to_storage(user_id, bio_data):
#     bios = load_bios()
#     uid = str(user_id)

#     bio_data["timestamp"] = datetime.now().isoformat()

#     bios[uid] = bio_data

#     cutoff = datetime.now() - timedelta(days=7)
#     bios = {
#         k: v for k, v in bios.items()
#         if "timestamp" in v and datetime.fromisoformat(v["timestamp"]) > cutoff
#     }

#     save_bios(bios)

def remove_bio_from_storage(user_id):
    bios = load_bios()
    uid = str(user_id)
    if uid in bios:
        del bios[uid]
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


# Initialize data
data = load_data()
jobs_by_country = data["jobs_by_country"]
skills_list = data["skills_list"]
