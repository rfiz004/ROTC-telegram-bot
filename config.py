
import os

# Bot Configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
# PORT = int(os.environ.get("PORT", 5000))
PORT = int(os.environ.get("PORT", 8443))

# GitHub Configuration
GITHUB_REPO = "rfiz004/ROTC-telegram-bot"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKENN")
GITHUB_BRANCH = "main"

# Admin Configuration
BIO_ADMIN_ID = 5890943003
BIO_CHANNEL = "@R_O_T_C_Bio"

# File Paths
BIOS_FILE = "bios.json"
DATA_FILE = "data.json"
RESERVATION_FILE = "job_reservations.json"

# Pagination
SKILLS_PER_PAGE = 12

# Countries
COUNTRIES = ["Aldemar", "Alpyr", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]

# Admin Passwords
RP_PASSWORDS = {
    "main_admin": "main",
    "bio_admin": "bio",
    "shop_admin": "shop"
}

# Chat IDs for invite links
ROLE_CHAT_ID = -1002616064737
REALCHAT_ID = -1002893489105
