
# import subprocess
# import glob
# from datetime import datetime
# from config import GITHUB_BRANCH, GITHUB_REPO_URL, GITHUB_TOKEN

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
from datetime import datetime
from config import GITHUB_BRANCH, GITHUB_REPO_URL, GITHUB_TOKEN

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
        # تنظیم user.name و user.email فقط برای این مخزن (local)
        subprocess.run(["git", "config", "user.name", "Render Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "render@example.com"], check=True)

        # چک کردن وجود برنچ و سوییچ کردن یا ساختن
        branches = subprocess.check_output(["git", "branch"]).decode()
        if GITHUB_BRANCH not in branches:
            subprocess.run(["git", "checkout", "-b", GITHUB_BRANCH], check=True)
        else:
            subprocess.run(["git", "checkout", GITHUB_BRANCH], check=True)

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
            "job_reservations.json"
        ]

        for pattern in files_to_add:
            for filepath in glob.glob(pattern):
                subprocess.run(["git", "add", "-f", filepath], check=True)

        status_output = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
        if not status_output:
            print("ℹ️ هیچ تغییری برای commit وجود ندارد.")
            return

        subprocess.run(["git", "commit", "-m", commit_message], check=True)

        # قبل از push → pull با rebase
        try:
            subprocess.run(["git", "pull", "--rebase", "origin", GITHUB_BRANCH], check=True)
        except subprocess.CalledProcessError:
            print("⚠️ کانفلیکت پیدا شد. انتخاب نسخه لوکال...")
            subprocess.run(["git", "rebase", "--abort"], check=True)
            subprocess.run(["git", "reset", "--hard", "HEAD"], check=True)
            subprocess.run(["git", "pull", "origin", GITHUB_BRANCH], check=True)
            # نگه داشتن تغییرات لوکال → force push
            subprocess.run(["git", "push", "origin", GITHUB_BRANCH, "--force"], check=True)
            print("✅ کانفلیکت با انتخاب نسخه لوکال حل شد و push انجام شد.")
            return

        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
        print("✅ فایل‌ها با موفقیت push شدند.")

    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای git: {e}")

