
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import COUNTRIES

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")]])

def restart_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔁 شروع مجدد", callback_data="back_to_main")]])

def back_and_home_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")],
        [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="back_to_main")]
    ])

def admin_back_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")],
        [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="back_to_main")]
    ])

def bio_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 لیست مشاغل", callback_data="admin_job_list")],
        [InlineKeyboardButton("📚 لیست مهارت‌ها", callback_data="admin_skill_list")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")]
    ])

def country_selection_keyboard(prefix):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"کشور {c}", callback_data=f"{prefix}_{c}")] for c in COUNTRIES] +
        [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")],
         [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="back_to_main")]]
    )

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 تحویل بیو", callback_data="bio")],
        [InlineKeyboardButton("🏰 مدیریت کشور", callback_data="manage_country")],
        [InlineKeyboardButton("⚙️ تنظیمات آرپی", callback_data="rp_settings")],
        [InlineKeyboardButton("📢 چنل‌های آرپی", callback_data="rp_channels")]
    ])

def country_jobs_keyboard():
    keyboard = [[InlineKeyboardButton(f"کشور {c}", callback_data=f"select_country_{c}")] for c in COUNTRIES]
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def job_management_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ اضافه کردن شغل", callback_data="add_job")],
        [InlineKeyboardButton("❌ حذف شغل", callback_data="remove_job")],
        [InlineKeyboardButton("🔼 افزایش ظرفیت", callback_data="increase_job")],
        [InlineKeyboardButton("🔽 کاهش ظرفیت", callback_data="decrease_job")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")],
        [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="back_to_main")]
    ])

def skill_management_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ اضافه کردن مهارت", callback_data="add_skill")],
        [InlineKeyboardButton("➖ حذف مهارت", callback_data="remove_skill")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")],
        [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="back_to_main")]
    ])

def skill_type_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📘 مهارت عادی", callback_data="skill_type_normal")],
        [InlineKeyboardButton("💠 مهارت خاص", callback_data="skill_type_special")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]
    ])

def bio_approval_keyboard(unique_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"approve_bio_{unique_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"reject_bio_{unique_id}")
        ]
    ])

def create_skill_selection_keyboard(page_skills, selected_skills, page, total_pages):
    keyboard = []
    row = []
    
    for i, skill in enumerate(page_skills):
        selected_mark = " ✅" if skill in selected_skills else ""
        row.append(InlineKeyboardButton(skill + selected_mark, callback_data=f"select_skill_{page}_{i}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"skill_page_{page - 1}"))
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"skill_page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Reset button if skills are selected
    if selected_skills:
        keyboard.append([InlineKeyboardButton("🗑 حذف انتخاب‌ها", callback_data="reset_skills")])

    # Continue button
    keyboard.append([InlineKeyboardButton("✅ ادامه", callback_data="skills_done")])

    return InlineKeyboardMarkup(keyboard)
