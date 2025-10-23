
# import subprocess
# import glob
# from datetime import datetime
# from config import GITHUB_BRANCH, GITHUB_REPO_URL, GITHUB_TOKEN

# import json
# from datetime import datetime

# def get_latest_province_update(province_file):
#     with open(province_file, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     latest_time = None
#     for prov in data:
#         t = prov.get("last_updated")  # تو همین فیلدی که اضافه کردی
#         if t:
#             t_dt = datetime.fromisoformat(t)
#             if not latest_time or t_dt > latest_time:
#                 latest_time = t_dt
#     return latest_time

# def get_latest_shop_update(shop_file):
#     with open(shop_file, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     latest_time = None
#     for item in data:
#         # created_at و updated_at هر دو وجود دارند
#         for key in ["created_at", "updated_at"]:
#             t = item.get(key)
#             if t:
#                 t_dt = datetime.fromisoformat(t)
#                 if not latest_time or t_dt > latest_time:
#                     latest_time = t_dt
#     return latest_time


# def get_latest_transfer_update(transfers_file):
#     with open(transfers_file, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     latest_time = None
#     for tr in data.get("transfers", []):
#         for key in ["requested_at", "approved_at", "delay_until"]:
#             t = tr.get(key)
#             if t:
#                 t_dt = datetime.fromisoformat(t)
#                 if not latest_time or t_dt > latest_time:
#                     latest_time = t_dt
#     return latest_time

# def get_github_latest_commit_timestamp(branch="main"):
#     output = subprocess.check_output(["git", "ls-remote", GITHUB_REPO_URL, branch]).decode()
#     # خروجی: hash \t refs/heads/main
#     # برای امن بودن، میشه hash رو بگیریم و با local مقایسه کنیم
#     return output.split()[0]  # hash آخرین commit


# def set_git_remote_url(url):
#     remotes = subprocess.check_output(["git", "remote"]).decode().split()
#     if "origin" in remotes:
#         subprocess.run(["git", "remote", "set-url", "origin", url], check=True)
#     else:
#         subprocess.run(["git", "remote", "add", "origin", url], check=True)

# def run_git_push():
#     if not GITHUB_TOKEN:
#         print("❌ GitHub token not found in environment variables!")
#         exit(1)

#     commit_message = f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

#     try:
#         # تنظیم user.name و user.email فقط برای این مخزن (local)
#         subprocess.run(["git", "config", "user.name", "Render Bot"], check=True)
#         subprocess.run(["git", "config", "user.email", "render@example.com"], check=True)

#         # چک کردن وجود برنچ و سوییچ کردن یا ساختن
#         branches = subprocess.check_output(["git", "branch"]).decode()
#         if GITHUB_BRANCH not in branches:
#             subprocess.run(["git", "checkout", "-b", GITHUB_BRANCH], check=True)
#         else:
#             subprocess.run(["git", "checkout", GITHUB_BRANCH], check=True)

#         set_git_remote_url(GITHUB_REPO_URL)

#         files_to_add = [
#             "provinces/*.json",
#             "EconomicItems/*.json",
#             "data/transfers.json",
#             "timers.json",
#             "shop_items.json",
#             "bios.json",
#             "block_shop.json",
#             "data.json",
#             "job_reservations.json"
#         ]

#         for pattern in files_to_add:
#             for filepath in glob.glob(pattern):
#                 subprocess.run(["git", "add", "-f", filepath], check=True)

#         status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
#         if not status_output:
#             print("ℹ️ هیچ تغییری برای commit وجود ندارد.")
#             return

#         subprocess.run(["git", "commit", "-m", commit_message], check=True)
#         subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
#         print("✅ فایل‌ها با موفقیت push شدند.")

#     except subprocess.CalledProcessError as e:
#         print(f"❌ خطا در اجرای git: {e}")
import subprocess
import glob
import json
from datetime import datetime
from config import GITHUB_BRANCH, GITHUB_REPO_URL, GITHUB_TOKEN


def get_latest_province_update(province_file):
    try:
        with open(province_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        t = data.get("last_updated")
        if t:
            return datetime.fromisoformat(t)
    except Exception as e:
        print(f"⚠️ خطا در بررسی {province_file}: {e}")
    return None


def get_latest_shop_update(shop_file):
    with open(shop_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    latest_time = None
    for item in data:
        for key in ["created_at", "updated_at"]:
            t = item.get(key)
            if t:
                t_dt = datetime.fromisoformat(t)
                if not latest_time or t_dt > latest_time:
                    latest_time = t_dt
    return latest_time


def get_latest_transfer_update(transfers_file):
    with open(transfers_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    latest_time = None
    for tr in data.get("transfers", []):
        for key in ["requested_at", "approved_at", "delay_until"]:
            t = tr.get(key)
            if t:
                t_dt = datetime.fromisoformat(t)
                if not latest_time or t_dt > latest_time:
                    latest_time = t_dt
    return latest_time


def get_latest_economic_update(econ_file):
    with open(econ_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    t = data.get("last_update_time")
    return datetime.fromisoformat(t) if t else None


def set_git_remote_url(url):
    remotes = subprocess.check_output(["git", "remote"]).decode().split()
    if "origin" in remotes:
        subprocess.run(["git", "remote", "set-url", "origin", url], check=True)
    else:
        subprocess.run(["git", "remote", "add", "origin", url], check=True)


def run_git_push():
    if not GITHUB_TOKEN:
        print("❌ GitHub token not found in environment variables!")
        exit(1)

    commit_message = f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        subprocess.run(["git", "config", "user.name", "Render Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "render@example.com"], check=True)

        # چک برنچ
        branches = subprocess.check_output(["git", "branch"]).decode()
        if GITHUB_BRANCH not in branches:
            subprocess.run(["git", "checkout", "-b", GITHUB_BRANCH], check=True)
        else:
            subprocess.run(["git", "checkout", GITHUB_BRANCH], check=True)

        set_git_remote_url(GITHUB_REPO_URL)

        # -------------------
        # Stash changes before rebase (حل مشکل unstaged changes)
        # -------------------
        subprocess.run(["git", "add", "-A"], check=False)
        subprocess.run(["git", "stash"], check=False)

        # -------------------
        # Fetch & rebase (برای گرفتن تغییرات جدید)
        # -------------------
        subprocess.run(["git", "fetch", "origin", GITHUB_BRANCH], check=True)
        subprocess.run(["git", "rebase", f"origin/{GITHUB_BRANCH}"], check=False)

        # -------------------
        # Restore stashed changes
        # -------------------
        subprocess.run(["git", "stash", "pop"], check=False)

        # -------------------
        # Files that need safe check
        # -------------------
        safe_files = {
            "provinces/*.json": get_latest_province_update,
            "shop_items.json": get_latest_shop_update,
            "data/transfers.json": get_latest_transfer_update,
            "EconomicItems/*.json": get_latest_economic_update,
        }

        for pattern, update_func in safe_files.items():
            for filepath in glob.glob(pattern):
                try:
                    local_time = update_func(filepath)
                    if local_time:
                        print(f"🕓 {filepath} | آخرین تغییر: {local_time}")
                    subprocess.run(["git", "add", "-f", filepath], check=True)
                except Exception as e:
                    print(f"⚠️ خطا در بررسی {filepath}: {e}")

        # -------------------
        # Always-push files
        # -------------------
        always_push_files = [
            "timers.json",
            "bios.json",
            "block_shop.json",
            "data.json",
            "job_reservations.json",
            "countries_data.json",
            "users.json"
        ]
        for pattern in always_push_files:
            for filepath in glob.glob(pattern):
                subprocess.run(["git", "add", "-f", filepath], check=True)

        # -------------------
        # Commit & Push
        # -------------------
        status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
        if not status_output:
            print("ℹ️ هیچ تغییری برای commit وجود ندارد.")
            return

        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
        print("✅ فایل‌ها با موفقیت push شدند.")

    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای git: {e}")
