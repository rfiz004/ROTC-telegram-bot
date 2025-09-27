
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
        subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
        print("✅ فایل‌ها با موفقیت push شدند.")

    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در اجرای git: {e}")


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

#         try:
#             subprocess.run(["git", "push", "origin", GITHUB_BRANCH], check=True)
#             print("✅ فایل‌ها با موفقیت push شدند.")
#         except subprocess.CalledProcessError as push_err:
#             print(f"❌ Push معمولی ناموفق بود: {push_err}")
#             print("⚠️ تلاش برای force push فقط فایل‌های JSON...")

#             json_patterns = [
#                 "provinces/*.json",
#                 "EconomicItems/*.json",
#                 "data/transfers.json",
#                 "timers.json",
#                 "shop_items.json",
#                 "bios.json",
#                 "block_shop.json",
#                 "data.json",
#                 "job_reservations.json"
#             ]

#             for pattern in json_patterns:
#                 for filepath in glob.glob(pattern):
#                     subprocess.run(["git", "add", "-f", filepath], check=True)

#             status_after_add = subprocess.check_output(["git", "status", "--porcelain"]).decode().strip()
#             if status_after_add:
#                 subprocess.run([
#                     "git", "commit", "-m",
#                     f"[auto-json-force] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
#                 ], check=True)

#             subprocess.run(["git", "push", "--force", "origin", GITHUB_BRANCH], check=True)
#             print("✅ Force push (JSON only) succeeded.")

#     except subprocess.CalledProcessError as e:
#         print(f"❌ خطا در اجرای git: {e}")

# # if __name__ == "__main__":
# #     run_git_push()
