import os

# ────────────── Token Configs
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

PORT = int(os.environ.get("PORT", 10000))

# ────────────── GitHub
GITHUB_REPO = "rfiz004/ROTC-telegram-bot"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKENN")  # یا GITHUB_TOKEN
GITHUB_BRANCH = "main"
GITHUB_REPO_URL = f"https://{GITHUB_TOKEN}@github.com/rfiz004/ROTC-telegram-bot.git"
# ────────────── Admin
BIO_ADMIN_ID = [5890943003, 898145344, 7217974527] #me-ali-mary
COUNTRY_ADMIN_ID = {
    "Alpyr": [1771323853],
    "Aldemar": [1771323853],
    "Walden": [1771323853],

    "Azure": [2121665497],
    "Hikada": [2121665497],
    "Alestria": [2121665497],

    "Santos": [1771323853],
    "Imperial": [2121665497],
    "Northwood": [1771323853],
}

BIO_CHANNEL = "@R_O_T_C_Bio"
CHANNEL_ID = "@R_O_T_C_News"
SHOP_CHANNEL = "@R_O_T_C_Shop"

RP_PASSWORDS = {
    "master_admin": "MASTER_2025",
    "bio_admin": "BIO_ADMIN_2025",
    "shop_admin": "SHOP_ADMIN_2025",
    "multi_admin_1": "ALDW_ADMIN_2025",  # Alpyr, Aldemar, Walden
    "multi_admin_2": "AZHI_ADMIN_2025",  # Azure, Hikada, Alestria
    "multi_admin_3": "NSIA_ADMIN_2025",  # Santos, Imperial, Northwood
}

# Multi-country admin mapping
COUNTRY_ADMINS = {
    "multi_admin_1": ["Aldemar", "Walden"],
    "multi_admin_2": ["Azure", "Hikada", "Alestria"],
    "multi_admin_3": ["Santos", "Imperial", "Northwood"],
}
for key, val in RP_PASSWORDS.items():
    if not val:
        raise ValueError(f"❌ Missing password for: {key}")

# ────────────── Files & App Settings
BIOS_FILE = "bios.json"
DATA_FILE = "data.json"
RESERVATION_FILE = "job_reservations.json"
SHOP_CHANNEL = "@R_O_T_C_Shop"  # Make sure bot is added as admin to this channel

SKILLS_PER_PAGE = 12
COUNTRIES = ["Aldemar", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]
LOCKED_JOBS = {
    "Santos": ["امپراتور"]
}

ROLE_CHAT_ID = -1002576512427
REALCHAT_ID = -1002885798901

# Capital cities mapping for international transfers
CAPITAL_CITIES = {
    "Alestria": "Alkyanos",
    "Hikada": "Shinrinky", 
    "Azure": "Kalindora",
    "Aldemar": "Marevenport",
    "Walden": "Verindel",
    "Northwood": "Trenhallough",
    "Santos": "Zahramun",
    "Imperial": "Lusauren"
}
