import subprocess
import glob
from datetime import datetime
from config import GITHUB_BRANCH, GITHUB_REPO_URL, GITHUB_TOKEN

def set_git_remote_url(url):
    # بررسی وجود ریموت origin و اضافه کردن یا ست کردن URL آن
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
        # ست کردن نام و ایمیل گیت (برای جلوگیری از خطای unable to auto-detect email)
        subprocess.run(["git", "config", "--global", "user.name", "Render Bot"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "render@example.com"], check=True)

        # تنظیم ریموت origin با توکن و URL
        set_git_remote_url(GITHUB_REPO_URL)

        files_to_add = [
            "provinces/*.json",
            "EconomicItems/*.json",
            "data/transfers.json",
            "timers.json",
            "shop_items.json",
            "bios.json",
            "block_shop.json",
            "data.json",
            "job_reservations.json",
        ]

        # اضافه کردن فایل‌های تغییر کرده
        for pattern in files_to_add:
            for filepath in glob.glob(pattern):
                subprocess.run(["git", "add", filepath], check=True)

        # بررسی اینکه آیا تغییری وجود دارد یا نه
        status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
        if not status_output:
            print("ℹ️ هیچ تغییری برای commit وجود ندارد.")
        else:
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
            print("✅ فایل‌ها با موفقیت push شدند.")

    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای git: {e}")
