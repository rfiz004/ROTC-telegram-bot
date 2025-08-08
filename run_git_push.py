import os
import subprocess
import glob
from datetime import datetime
from config import GITHUB_BRANCH, GITHUB_REPO, GITHUB_TOKEN, GITHUB_REPO_URL

def run_git_push():
    if not GITHUB_TOKEN:
        print("❌ GitHub token not found in environment variables!")
        exit(1)

    # GITHUB_REPO_URL = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
    commit_message = f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    try:
        subprocess.run(["git", "remote", "set-url", "origin", GITHUB_REPO_URL], check=True)

        files_to_add = [
            "provinces/*.json",
            "EconomicItems/*.json"
            "data/transfers.json",
            "timers.json",
            "shop_items.json",
            "bios.json",
            "block_shop.json",
            "data.json",
            "job_reservations.json",
        ]

        for pattern in files_to_add:
            for filepath in glob.glob(pattern):
                subprocess.run(["git", "add", filepath], check=True)

        status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
        if not status_output:
            print("ℹ️  هیچ تغییری برای commit وجود ندارد.")
        else:
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
            print("✅ فایل‌ها با موفقیت push شدند.")

    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای git: {e}")
