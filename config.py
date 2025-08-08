import os

# ────────────── Token Configs
BOT_TOKEN = os.environ.get("BOT_TOKEN","8135083594:AAHb7wdYeUsVnNaCjPoP9ZYSTlDSJGcJhEs")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing!")

# Use port 5000 for Replit compatibility
PORT = int(os.environ.get("PORT", 10000))

# ────────────── Platform Detection
# Check if running on Replit
IS_REPLIT = os.environ.get("REPL_SLUG") is not None
REPLIT_URL = f"https://{os.environ.get('REPL_SLUG', 'unknown')}.{os.environ.get('REPL_OWNER', 'unknown')}.repl.co" if IS_REPLIT else None

# Force polling mode for Replit compatibility
USE_POLLING = True

# ────────────── GitHub
GITHUB_REPO = "rfiz004/ROTC-telegram-bot"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKENN")  # یا GITHUB_TOKEN
GITHUB_BRANCH = "main"

# ────────────── Admin
BIO_ADMIN_ID = [5890943003, 898145344] #me-ali-mary
COUNTRY_ADMIN_ID = {
    "Alpyr": [1771323853],
    "Aldemar": [1771323853],
    "Walden": [1771323853],

    "Azure": [2121665497],
    "Hikada": [2121665497],
    "Alestria": [2121665497],

    "Santos": [898145344],
    "Imperial": [898145344],
    "Northwood": [898145344],
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
    "multi_admin_1": ["Alpyr", "Aldemar", "Walden"],
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
COUNTRIES = ["Aldemar", "Alpyr", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]
LOCKED_JOBS = {
    "Santos": ["امپراتور"]
}

ROLE_CHAT_ID = -1002576512427
REALCHAT_ID = -1002885798901

# Capital cities mapping for international transfers
CAPITAL_CITIES = {
    "Alestria": "Alkyanos",
    "Hikada": "Shinrinky", 
    "Azure": "Azureus",
    "Aldemar": "Marevenport",
    "Alpyr": "Eldhalm",
    "Walden": "Verindel",
    "Northwood": "Trenhallough",
    "Santos": "Zahramun",
    "Imperial": "Kalindora",
    "Imperial": "Lusauren",
    "Santos": "Zahramun",
    "Northwood": "Trenhallough",
    "Walden": "Verindel",
    "Aldemar": "Marevenport",
    "Alpyr": "Eldhalm"
}
