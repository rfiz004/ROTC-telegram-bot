from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import COUNTRIES


SKILLS_PER_PAGE = 12

def main_menu():
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📝 ثبت بیوگرافی", callback_data="submit_bio")],
        [InlineKeyboardButton("🏛 مدیریت کشور", callback_data="manage_country")],
        [InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_menu")],
        [InlineKeyboardButton("📢 چنل‌های آرپی", callback_data="rp_channels")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_and_home_buttons():
    """Create back and home navigation buttons"""
    keyboard = [
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")]
    ]
    return InlineKeyboardMarkup(keyboard)

def restart_button():
    """Create restart button"""
    keyboard = [
        [InlineKeyboardButton("🔄 شروع دوباره", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_back_buttons():
    """Create admin back buttons"""
    keyboard = [
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def country_jobs_keyboard():
    """Create keyboard for country selection in bio submission"""
    keyboard = []
    countries = ["Aldemar", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🏛 {country}", callback_data=f"select_bio_country_{country}")])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# def bio_admin_menu():
#     """Create bio admin menu keyboard"""
#     keyboard = [
#         [InlineKeyboardButton("👥 مدیریت مشاغل", callback_data="admin_jobs")],
#         [InlineKeyboardButton("🛠 مدیریت مهارت‌ها", callback_data="admin_skills")],
#         [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="start_fresh")]
#     ]
#     return InlineKeyboardMarkup(keyboard)

# def master_admin_menu():
#     """Master admin menu with full access"""
#     keyboard = [
#         [InlineKeyboardButton("💼 مدیریت مشاغل", callback_data="admin_jobs")],
#         [InlineKeyboardButton("🎯 مدیریت مهارت‌ها", callback_data="admin_skills")],
#         [InlineKeyboardButton("🏰 مدیریت استان‌ها", callback_data="admin_province_menu")],
#         [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
#     ]
#     return InlineKeyboardMarkup(keyboard)


def bio_admin_menu():
    """Create bio admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("👥 مدیریت مشاغل", callback_data="admin_jobs")],
        [InlineKeyboardButton("🛠 مدیریت مهارت‌ها", callback_data="admin_skills")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def master_admin_menu():
    """Master admin menu with full access"""
    keyboard = [
        [InlineKeyboardButton("💼 مدیریت مشاغل", callback_data="admin_jobs")],
        [InlineKeyboardButton("🎯 مدیریت مهارت‌ها", callback_data="admin_skills")],
        [InlineKeyboardButton("🏰 مدیریت استان‌ها", callback_data="admin_province_menu")],
        [InlineKeyboardButton("🏗 مدیریت وضعیت سازه‌ها", callback_data="admin_structure_status")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def shop_admin_menu():
    """Shop admin menu"""
    keyboard = [
        [InlineKeyboardButton("🛒 مدیریت فروشگاه", callback_data="admin_manage_shop")],
        [InlineKeyboardButton("➕ افزودن آیتم جدید", callback_data="admin_add_shop_item")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def multi_country_admin_menu(countries):
    """Create multi-country admin menu keyboard"""
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 مدیریت {country.capitalize()}", callback_data=f"admin_country_menu_{country}")])
    keyboard.append([InlineKeyboardButton("🏰 همه استان‌ها", callback_data="admin_view_all_provinces")])
    keyboard.append([InlineKeyboardButton("🔄 همه انتقالات", callback_data="admin_manage_transfers")])
    keyboard.append([InlineKeyboardButton("🏗 مدیریت وضعیت سازه‌ها", callback_data="admin_structure_status")])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def manage_country_menu():
    """Country management menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏰 نمایش استان", callback_data="country_overview")],
        [InlineKeyboardButton("📊 نمای کلی اقتصاد", callback_data="admin_economy_overview")],
        [InlineKeyboardButton("💰 ویرایش مالیات", callback_data="edit_tax")],
        [InlineKeyboardButton("🍞 مدیریت مصرف غلات", callback_data="manage_food_menu")],
        [InlineKeyboardButton("📢 اعلامیه", callback_data="country_news")],
        [InlineKeyboardButton("🛍 فروشگاه", callback_data="open_shop")],
        [InlineKeyboardButton("🔄 انتقالات", callback_data="transfer_menu")],
        [InlineKeyboardButton("🏠 صفحه اصلی", callback_data="start_fresh")]
    ]
    return InlineKeyboardMarkup(keyboard)


def manage_food_menu():
    """Keyboard for food management per province"""
    keyboard = [
        [InlineKeyboardButton("📋 تعیین اولویت غلات", callback_data="set_grain_priority")],
        [InlineKeyboardButton("⚙️ تعیین درصد مصرف", callback_data="set_grain_consumption")],
        [InlineKeyboardButton("🔍 پیش‌نمایش مصرف", callback_data="preview_grain_effect")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")]

    ]
    return InlineKeyboardMarkup(keyboard)



def country_selection_keyboard(prefix):
    """Create country selection keyboard for admin"""
    countries = ["Aldemar", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"{prefix}_{country}")])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")])
    return InlineKeyboardMarkup(keyboard)

def job_management_keyboard(country):
    """Create job management keyboard for a specific country"""
    keyboard = [
        [InlineKeyboardButton("➕ افزودن شغل", callback_data=f"add_job_{country}")],
        [InlineKeyboardButton("➖ حذف شغل", callback_data=f"remove_job_{country}")],
        [InlineKeyboardButton("⬆️ افزایش ظرفیت", callback_data=f"increase_job_{country}")],
        [InlineKeyboardButton("⬇️ کاهش ظرفیت", callback_data=f"decrease_job_{country}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_jobs")]
    ]
    return InlineKeyboardMarkup(keyboard)

def skill_management_keyboard():
    """Create skill management keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ افزودن مهارت", callback_data="add_skill")],
        [InlineKeyboardButton("➖ حذف مهارت", callback_data="remove_skill")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def skill_type_selection_keyboard():
    """Create skill type selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("📘 مهارت عادی", callback_data="skill_type_normal")],
        [InlineKeyboardButton("💠 مهارت خاص", callback_data="skill_type_special")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


# def skill_type_selection_keyboard(back_cb="back_to_admin_menu"):
#     keyboard = [
#         [InlineKeyboardButton("📘 مهارت عادی", callback_data="skill_type_normal")],
#         [InlineKeyboardButton("💠 مهارت خاص", callback_data="skill_type_special")],
#         [InlineKeyboardButton("🔙 برگشت", callback_data=back_cb)]
#     ]
#     return InlineKeyboardMarkup(keyboard)

def bio_approval_keyboard(unique_id):
    """Create bio approval keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ تایید", callback_data=f"approve_bio_{unique_id}")],
        [InlineKeyboardButton("❌ رد", callback_data=f"reject_bio_{unique_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def news_type_menu():
    keyboard = [
        [InlineKeyboardButton("📰 اعلامیه عادی", callback_data="news_normal")],
        [InlineKeyboardButton("⚔️ اعلام جنگ", callback_data="news_war")],
        [InlineKeyboardButton("🚫 تحریم", callback_data="news_sanction")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def select_country_menu(countries=None):
    """Create country selection menu for admins"""
    if countries is None:
        countries = ["Aldemar", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]

    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"admin_select_country_{country}")])

    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def select_province_menu(provinces):
    keyboard = []
    for province in provinces:
        keyboard.append([InlineKeyboardButton(f"🏰 {province}", callback_data=f"target_province_{province}")])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")])
    return InlineKeyboardMarkup(keyboard)

def target_country_keyboard(countries, news_type):
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"target_country_{country}")])
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_country_menu")])
    return InlineKeyboardMarkup(keyboard)

# def create_skill_selection_keyboard(page_skills, selected, page, total_pages):
#     """Create skill selection keyboard with pagination"""
#     keyboard = []

#     # Add skill buttons
#     for i, skill in enumerate(page_skills):
#         mark = "✅ " if skill in selected else ""
#         keyboard.append([InlineKeyboardButton(
#             f"{mark}{skill}", 
#             callback_data=f"select_skill_{page}_{i}"
#         )])

#     # Navigation buttons
#     nav_buttons = []
#     if page > 0:
#         nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"skill_page_{page-1}"))
#     if page < total_pages - 1:
#         nav_buttons.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"skill_page_{page+1}"))

#     if nav_buttons:
#         keyboard.append(nav_buttons)

#     # Control buttons
#     control_buttons = []
#     control_buttons.append(InlineKeyboardButton("🔄 ریست", callback_data="reset_skills"))
#     control_buttons.append(InlineKeyboardButton("✅ ادامه", callback_data="skills_done"))
#     keyboard.append(control_buttons)

#     keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])

#     return InlineKeyboardMarkup(keyboard)

def create_skill_selection_keyboard(page_skills, selected, page, total_pages):
    """Create skill selection keyboard with pagination"""
    keyboard = []

    # Add skill buttons in 3 columns (i.e., 4 rows per page)
    row = []
    for i, skill in enumerate(page_skills):
        mark = "✅ " if skill in selected else ""
        button = InlineKeyboardButton(
            f"{mark}{skill}", 
            callback_data=f"select_skill_{page}_{i}"
        )
        row.append(button)
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)  # add remaining buttons if not full row

    # Navigation buttons (Previous/Next)
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"skill_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"skill_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Control buttons (Reset/Done)
    control_buttons = [
        InlineKeyboardButton("🔄 ریست", callback_data="reset_skills"),
        InlineKeyboardButton("✅ ادامه", callback_data="skills_done"),
    ]
    keyboard.append(control_buttons)

    # Back button
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])

    return InlineKeyboardMarkup(keyboard)


def skills_keyboard(skills_list, selected_skills, page=0):
    """Create skill selection keyboard with exactly 12 skills per page"""
    # Calculate start and end for current page
    start = page * SKILLS_PER_PAGE
    end = start + SKILLS_PER_PAGE
    page_skills = skills_list[start:end]

    buttons = []
    # Skills buttons (3 per row for better layout with 12 skills)
    for i in range(0, len(page_skills), 3):
        row = []
        for j in range(3):
            if i + j < len(page_skills):
                skill = page_skills[i + j]
                if skill in selected_skills:
                    row.append(InlineKeyboardButton(f"✅ {skill}", callback_data=f"select_skill_{skill}"))
                else:
                    row.append(InlineKeyboardButton(skill, callback_data=f"select_skill_{skill}"))
        if row:  # Only add non-empty rows
            buttons.append(row)

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"skill_page_{page-1}"))

    if end < len(skills_list):
        nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"skill_page_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    # Bottom buttons
    buttons.append([
        InlineKeyboardButton("🔄 ریست", callback_data="reset_skills"),
        InlineKeyboardButton("✅ تأیید", callback_data="skills_done")
    ])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_previous")])

    return InlineKeyboardMarkup(buttons)

def country_menu_keyboard():
    """Country management menu keyboard"""
    buttons = [
        [InlineKeyboardButton("📰 اخبار کشور", callback_data="news_management")],
        [InlineKeyboardButton("💰 وضعیت اقتصادی", callback_data="economy_status")],
        [InlineKeyboardButton("🏪 فروشگاه", callback_data="open_shop")],
        [InlineKeyboardButton("📦 سیستم انتقالات", callback_data="transfer_menu")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def province_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏰 نمایش همه استان‌ها", callback_data="admin_view_all_provinces")],
        [InlineKeyboardButton("✏️ ویرایش استان", callback_data="admin_edit_province")],
        [InlineKeyboardButton("🔄 مدیریت انتقالات", callback_data="admin_manage_transfers")],
        [InlineKeyboardButton("🛒 مدیریت فروشگاه", callback_data="admin_manage_shop")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_previous")]
    ])

def admin_edit_province():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ایجاد استان جدید", callback_data="admin_create_province")],
        [InlineKeyboardButton("🔄 مدیریت انتقالات", callback_data="admin_manage_transfers")],
        [InlineKeyboardButton("🛒 مدیریت فروشگاه", callback_data="admin_manage_shop")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_rp_settings")]
    ])

def country_admin_menu(country):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏰 مدیریت استان‌های {country}", callback_data=f"admin_country_provinces_{country}")],
        [InlineKeyboardButton(f"🔄 انتقالات {country}", callback_data=f"admin_country_transfers_{country}")],
        [InlineKeyboardButton(f"🛒 فروشگاه {country}", callback_data=f"admin_country_shop_{country}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_rp_settings")]
    ])

