"""
Bio handler module - handles character biography functionality
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from datetime import datetime, timedelta
import re
from data_manager import jobs_by_country, skills_config, save_data, add_bio_to_storage, get_used_hashtags, add_used_hashtag, load_job_reservations, save_job_reservations, load_bios, save_bios, load_data_file
from keyboards import country_jobs_keyboard, create_skill_selection_keyboard, bio_approval_keyboard, restart_button
from utils import calculate_skill_pages, get_page_skills, validate_age, validate_hashtag, validate_username, format_bio_text
from config import BIO_ADMIN_ID, SKILLS_PER_PAGE, COUNTRIES
from skills_text import SKILLS_DESCRIPTION_TEXT

logger = logging.getLogger(__name__)

async def handle_bio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bio menu operations"""
    query = update.callback_query
    await query.answer()

    # Placeholder implementation
    await query.edit_message_text("🎭 سیستم بیوگرافی در حال توسعه است...")

async def create_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create new character biography"""
    # Placeholder implementation
    await update.message.reply_text("ایجاد بیوگرافی در حال حاضر در دسترس نیست.")

async def edit_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit existing biography"""
    # Placeholder implementation
    await update.message.reply_text("ویرایش بیوگرافی در حال حاضر در دسترس نیست.")

async def view_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View biography"""
    # Placeholder implementation
    await update.message.reply_text("مشاهده بیوگرافی در حال حاضر در دسترس نیست.")


async def start_bio_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bio submission process"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Check if user already has a pending bio
    bios = load_bios()
    if str(user_id) in bios.get("bios", {}):
        try:
            await query.message.edit_text("⏳ شما قبلاً یک بیو ثبت کرده‌اید. لطفاً منتظر بمانید تا ادمین آن را بررسی کند.")
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise e
        return

    # Set bio flow
    context.user_data[user_id] = {"step": "selecting_country", "flow_type": "bio"}

    try:
        await query.message.edit_text("برای کدوم کشور می‌خوای بیو بدی؟", reply_markup=country_jobs_keyboard())
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message content is the same, ignore the error
            pass
        else:
            raise e

async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show country selection for bio"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Check if user already has a pending bio
    bios = load_bios()
    if str(user_id) in bios.get("bios", {}):
        try:
            await query.message.edit_text("⏳ شما قبلاً یک بیو ثبت کرده‌اید. لطفاً منتظر بمانید تا ادمین آن را بررسی کند.")
        except BadRequest as e:
            if "Message is not modified" in str(e):
                pass
            else:
                raise e
        return

    # Set bio flow
    context.user_data[user_id] = {"step": "selecting_country", "flow_type": "bio"}

    try:
        await query.message.edit_text("برای کدوم کشور می‌خوای بیو بدی؟", reply_markup=country_jobs_keyboard())
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message content is the same, ignore the error
            pass
        else:
            raise e

async def select_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Extract country from bio-specific callback data
    if query.data.startswith("select_bio_country_"):
        country = query.data.replace("select_bio_country_", "")
    else:
        await query.message.edit_text("❌ خطا در انتخاب کشور برای بیو.")
        return

    context.user_data[user_id] = {"step": "selecting_job", "country": country, "flow_type": "bio"}

    job_buttons = []
    job_text = "👥 مشاغلی که داریم:\n"
    #jobs = jobs_by_country[country]
    data = load_data_file("data.json")
    jobs_by_country = data.get("jobs_by_country", {})
    jobs = jobs_by_country.get(country, [])


    # بررسی اینکه آیا "شاه" پر شده
    king_taken = any(job["name"] == "شاه" and job["count"] == 0 for job in jobs)

    for job in jobs:
        name = job["name"]
        level = job["level"]
        count = job["count"]

        if country == "Santos" and name == "امپراتور":
            job_buttons.append([InlineKeyboardButton(f"{name} 🔒 (قفل شده)", callback_data="job_azure_locked")])
            job_text += f"🔒 {name} - لول: {level} - قابل انتخاب نیست\n"
            continue 

        # ⚠️ قفل کردن دوک اعظم در صورت پر بودن شاه
        if name == "دوک اعظم" and king_taken:
            job_buttons.append([InlineKeyboardButton(f"{name} ❌ (غیرقابل انتخاب)", callback_data="job_locked")])
            job_text += f"🔒 {name} - لول: {level} - در حال حاضر قابل انتخاب نیست\n"
        elif count > 0:
            # Use safe job name for callback (replace spaces and special chars)
            safe_job_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("ک", "k").replace("گ", "g")
            job_buttons.append([InlineKeyboardButton(f"{name} (لول {level})", callback_data=f"bio_job_{safe_job_name}")])
            job_text += f"🔹 {name} - لول: {level} - ظرفیت: {count} نفر\n"
        else:
            job_buttons.append([InlineKeyboardButton(f"{name} ❌ (پر شده)", callback_data="job_taken")])
            job_text += f"❌ {name} - لول: {level} - ظرفیت پر شده\n"

    job_text += '\n\n 🔖با انتخاب شغل آزاد میتونین بعدا از ادمین بخواین شغلی که مرتبط با کارهای حکومتی نیست رو براتون توی بیو ادیت بزنه (بعد تایید البته)'
    job_text += '\n\n📌توضیحات مشاغل هر کشور رو توی <a href="https://t.me/R_O_T_C_Dignitaries">چنل اطلاعات کشورها</a> ببین.'

    job_buttons.append([InlineKeyboardButton("🔙 برگشتن", callback_data="back_to_main")])

    try:
        await query.message.edit_text(job_text, reply_markup=InlineKeyboardMarkup(job_buttons), parse_mode='HTML')
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message content is the same, ignore the error
            pass
        else:
            raise e

async def handle_job_locks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "job_locked":
        await query.answer("❌ این مقام به دلیل انتخاب شدن پادشاه قابل دسترسی نیست.", show_alert=True)
    elif query.data == "job_azure_locked":
        await query.answer("❌ این مقام در حال حاضر قابل دسترسی نیست.", show_alert=True)
    elif query.data == "job_taken":
        await query.answer("❌ این مقام ظرفیتش پر شده.", show_alert=True)

# async def ask_bio_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     if query.data in ["job_locked", "job_azure_locked", "job_taken"]:
#         await query.answer("❌ این مقام در حال حاضر قابل دسترسی نیست.", show_alert=True)
#         return
#     await query.answer()
#     user_id = query.from_user.id
#     job_safe = query.data[8:]  # Remove "bio_job_" prefix (safe name)
#     country = context.user_data["country"]

#     # Convert safe job name back to actual job name
#     job = job_safe.replace("_", " ").replace("k", "ک").replace("g", "گ")

#     # Handle special cases where the conversion might not be perfect
#     job_mapping = {
#         "گرند_دوک": "گرند دوک",
#         "دوک_اعظم": "دوک اعظم",
#         "grand_duk": "گرند دوک",
#         "duk_azam": "دوک اعظم"
#     }
#     job = job_mapping.get(job_safe, job)

#     # Check if user already has a pending bio
#     bios = load_bios()
#     if str(user_id) in bios.get("bios", {}):
#         await query.message.edit_text("⏳ شما قبلاً یک بیو ثبت کرده‌اید. لطفاً منتظر بمانید تا ادمین آن را بررسی کند.")
#         return

#     # Release any existing reservation for this user
#     reservations = load_job_reservations()
#     if str(user_id) in reservations:
#         old_reservation = reservations[str(user_id)]
#         old_country = old_reservation["country"]
#         old_job = old_reservation["job"]

#         # Return the old job to available pool
#         old_job_data = next((j for j in jobs_by_country.get(old_country, []) if j["name"] == old_job), None)
#         if old_job_data:
#             old_job_data["count"] += 1

#     context.user_data[user_id]["job"] = job

#     job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)
#     if job_data:
#         job_data["count"] = max(0, job_data["count"] - 1)

#         save_data("data.json", {
#             "jobs_by_country": jobs_by_country,
#             "skills_config": skills_config
#         })

#         reservations[str(user_id)] = {
#             "country": country,
#             "job": job,
#             "reserved_at": datetime.utcnow().isoformat()
#         }
#         save_job_reservations(reservations)

#         # Set expiration time and step
#         context.user_data[user_id]["expires_at"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
#         context.user_data[user_id]["step"] = "asking_name"

#         # Delete the job selection message to avoid confusion
#         try:
#             await query.message.delete()
#         except BadRequest as e:
#             if "Message to delete not found" not in str(e):
#                 print(f"Failed to delete job selection message: {e}")

#         # Send separate messages
#         await context.bot.send_message(
#             chat_id=query.message.chat_id,
#             text="⏳ از این لحظه 30 دقیقه فرصت داری فرم بیوت رو کامل کنی. اگر دیر بجنبی شغل رزرو شده آزاد میشه!"
#         )
#         await context.bot.send_message(
#             chat_id=query.message.chat_id,
#             text="📛بچه خوشگل اسم کارکترتو کخ کن بیاد"
#         )
#     else:
#         await query.message.edit_text("❌ مشکلی پیش اومده. شغلی که انتخاب کردی وجود نداره.")


async def ask_bio_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data in ["job_locked", "job_azure_locked", "job_taken"]:
        await query.answer("❌ این مقام در حال حاضر قابل دسترسی نیست.", show_alert=True)
        return
    await query.answer()

    user_id = query.from_user.id
    job_safe = query.data[8:]  # حذف "bio_job_" از اول

    user_data = context.user_data.get(user_id)
    if user_data is None:
        await query.message.edit_text("لطفاً ابتدا کشور خود را انتخاب کنید.")
        return

    country = user_data.get("country")
    if not country:
        await query.message.edit_text("لطفاً ابتدا کشور خود را انتخاب کنید.")
        return

    # تبدیل نام شغل امن به شغل اصلی
    job = job_safe.replace("_", " ").replace("k", "ک").replace("g", "گ")

    job_mapping = {
        "گرند_دوک": "گرند دوک",
        "دوک_اعظم": "دوک اعظم",
        "grand_duk": "گرند دوک",
        "duk_azam": "دوک اعظم"
    }
    job = job_mapping.get(job_safe, job)

    # بارگذاری بیوها و چک کردن بیوی نیمه‌کاره
    bios = load_bios()
    if str(user_id) in bios.get("bios", {}):
        bio = bios["bios"][str(user_id)]
        # فقط وقتی که مرحله بیو pending هست اجازه نده ادامه بده
        if bio.get("step") == "pending":
            await query.message.edit_text("⏳ شما قبلاً یک بیو ثبت کرده‌اید. لطفاً منتظر بمانید تا ادمین آن را بررسی کند.")
            return

    # آزاد کردن رزرو قبلی
    reservations = load_job_reservations()
    if str(user_id) in reservations:
        old_reservation = reservations[str(user_id)]
        old_country = old_reservation.get("country")
        old_job = old_reservation.get("job")

        old_job_data = next((j for j in jobs_by_country.get(old_country, []) if j["name"] == old_job), None)
        if old_job_data:
            old_job_data["count"] += 1

    # ذخیره شغل انتخاب شده
    if user_id not in context.user_data:
        context.user_data[user_id] = {}
    context.user_data[user_id]["job"] = job

    job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job), None)
    if job_data:
        job_data["count"] = max(0, job_data["count"] - 1)

        save_data("data.json", {
            "jobs_by_country": jobs_by_country,
            "skills_config": skills_config
        })

        reservations[str(user_id)] = {
            "country": country,
            "job": job,
            "reserved_at": datetime.utcnow().isoformat()
        }
        save_job_reservations(reservations)


        # ذخیره اولیه‌ی بیو ناقص با کشور و شغل و مرحله
        bios.setdefault("bios", {})
        bios["bios"][str(user_id)] = {
            "country": country,
            "job": job,
            "step": "asking_name",
            "flow_type": "bio",
            "saved_at": datetime.utcnow().isoformat(),
        }
        save_bios(bios)

        context.user_data[user_id]["expires_at"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        context.user_data[user_id]["step"] = "asking_name"

        try:
            await query.message.delete()
        except BadRequest as e:
            if "Message to delete not found" not in str(e):
                print(f"Failed to delete job selection message: {e}")

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ از این لحظه 30 دقیقه فرصت داری فرم بیوت رو کامل کنی. اگر دیر بجنبی شغل رزرو شده آزاد میشه!"
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📛 بچه خوشگل اسم کارکترتو کخ کن بیاد"
        )
    else:
        await query.message.edit_text("❌ مشکلی پیش اومده. شغلی که انتخاب کردی وجود نداره.")


async def show_skill_selection(update, context, page=0):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        message = update.message
        user_id = message.from_user.id

    current = context.user_data.setdefault(user_id, {})

    # نمایش توضیح مهارت‌ها فقط یک بار
    if not current.get("skills_description_sent"):
        if update.callback_query:
            await query.message.reply_text(SKILLS_DESCRIPTION_TEXT)
        else:
            await message.reply_text(SKILLS_DESCRIPTION_TEXT)
        current["skills_description_sent"] = True

    current = context.user_data[user_id]
    selected = current.get("skills", [])
    all_skills = skills_config["normal"] + skills_config["special"]
    total_pages = calculate_skill_pages(all_skills)

    context.user_data.setdefault(user_id, {})["skill_page"] = page

    # Skills for this page
    page_skills = get_page_skills(all_skills, page)

    # Store skills by page in context
    if 'skills_by_page' not in context.user_data:
        context.user_data['skills_by_page'] = {}
    context.user_data['skills_by_page'][page] = page_skills

    # Create keyboard
    keyboard = create_skill_selection_keyboard(page_skills, selected, page, total_pages)

    # Text
    selected = context.user_data.get(user_id, {}).get("skills", [])
    base_limit = 3

    # بررسی اینکه مهارت مدیریت امور داخلی انتخاب شده یا نه
    extended_skills = skills_config.get("extended_limit_if_has", {})
    for skill, new_limit in extended_skills.items():
        if skill in selected:
            base_limit = new_limit
            break

    skill_text = f"🔧 مهارت‌هات رو انتخاب کن (حداکثر {base_limit}):"

    if selected:
        skill_text += "\n✅ انتخاب‌شده‌ها:\n" + "\n".join(f"🔹 {s}" for s in selected)
    else:
        skill_text += "\n⚠️ فعلاً مهارتی انتخاب نشده."

    # Send or edit message
    if update.callback_query:
        try:
            await query.message.edit_text(skill_text, reply_markup=keyboard)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                # Message content is the same, ignore the error
                pass
            else:
                raise e
    else:
        await update.message.reply_text(skill_text, reply_markup=keyboard)

async def handle_skill_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    match = re.match(r"select_skill_(\d+)_(\d+)", query.data)
    if not match:
        await query.answer("❌ خطا در پردازش.", show_alert=True)
        return

    page_str, index_str = match.groups()
    page = int(page_str)
    index = int(index_str)

    skills_by_page = context.user_data.get("skills_by_page", {})
    page_skills = skills_by_page.get(page, [])

    if index >= len(page_skills):
        await query.answer("❌ مهارت پیدا نشد.", show_alert=True)
        return

    skill = page_skills[index]
    state = context.user_data.get(user_id, {})
    selected = state.get("skills", [])

    special_skills = skills_config["special"]
    allowed_extra_skills = [
        "آهنگری",
        "ساختمان‌سازی",
        "کشتی سازی",
        "ساخت دارو و سم",
        "جواهر سازی"
    ]

    extended_skills = skills_config.get("extended_limit_if_has", {})
    has_extended = any(ext in selected for ext in extended_skills)
    total_limit = 5 if has_extended else 3

    # حذف انتخاب اگر قبلا انتخاب شده
    if skill in selected:
        selected.remove(skill)
        state["skills"] = selected
        for i in range(1, 6):
            state.pop(f"skill{i}", None)
        for i, s in enumerate(selected, start=1):
            state[f"skill{i}"] = s
        context.user_data[user_id] = state
        await show_skill_selection(update, context, page=page)
        return

    special_count = sum(1 for s in selected if s in special_skills)
    extra_count = sum(1 for s in selected if s in allowed_extra_skills)

    # سقف کلی
    if len(selected) >= total_limit:
        await query.answer(f"⚠️ نمی‌تونی بیشتر از {total_limit} مهارت انتخاب کنی!", show_alert=True)
        return

    # مهارت خاص فقط 1 تا
    if skill in special_skills and special_count >= 1:
        await query.answer("⚠️ فقط می‌تونی یک مهارت خاص انتخاب کنی!", show_alert=True)
        return

    # شرط جدید: وقتی مدیریت داری و تعداد انتخاب‌ها به سقف نزدیکه، فقط مهارت فنی می‌تونی انتخاب کنی تا ۲ مهارت فنی داشته باشی
    if has_extended:
        selected_count = len(selected)
        if selected_count >= total_limit - 2:
            if skill not in allowed_extra_skills:
                if extra_count < 2:
                    await query.answer(
                        "⚠️ چون مهارت مدیریت امور داخلی برداشتی باید دو مهارت اضافه ت رو از بین مهارت های سازنده انتخاب کنی.",
                        show_alert=True
                    )
                    return
    

    # پیش‌نیازها
    required_skills_for = skills_config.get("required_skills_for", {})
    if skill in required_skills_for:
        required = required_skills_for[skill]
        missing = [r for r in required if r not in selected]
        if missing:
            await query.answer(
                f"⚠️ برای انتخاب «{skill}» باید اول این مهارت‌ها رو داشته باشی:\n" +
                "\n".join(f"🔸 {m}" for m in missing),
                show_alert=True
            )
            return

    # اضافه کردن مهارت
    selected.append(skill)
    state["skills"] = selected
    for i in range(1, 6):
        state.pop(f"skill{i}", None)
    for i, s in enumerate(selected, start=1):
        state[f"skill{i}"] = s

    context.user_data[user_id] = state
    await show_skill_selection(update, context, page=page)



async def handle_skill_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            raise
    user_id = query.from_user.id
    page = int(query.data.split("_")[-1])
    context.user_data.setdefault(user_id, {})["skill_page"] = page
    await show_skill_selection(update, context, page)
    print(f"[Skill Nav] User {user_id} → Page {page}")

async def handle_skill_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    context.user_data[user_id]["skill_page"] = 0
    context.user_data[user_id]["skills"] = []
    await show_skill_selection(update, context, page=0)

async def handle_skill_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # await query.answer()
    user_id = query.from_user.id
    state = context.user_data.get(user_id, {})
    selected = state.get("skills", [])

    if not selected:
        await query.answer("⚠️ حداقل سه مهارت انتخاب کن!", show_alert=True)
        return

    # Calculate the required skill limit based on selected skills
    base_limit = 3
    extended_skills = skills_config.get("extended_limit_if_has", {})
    for extended_skill, new_limit in extended_skills.items():
        if extended_skill in selected:
            base_limit = new_limit
            break

    # Check if user has selected the required number of skills
    if len(selected) < base_limit:
        await query.answer(f"⚠️ باید دقیقاً {base_limit} مهارت انتخاب کنی! فعلاً {len(selected)} تا انتخاب کردی.", show_alert=True)
        return

    # ذخیره مهارت‌ها با کلیدهای مجزا
    for i in range(1, 6):
        state.pop(f"skill{i}", None)

    for i, skill in enumerate(selected, start=1):
        state[f"skill{i}"] = skill

    context.user_data[user_id] = state
    state["step"] = "asking_appearance"
    try:
        await query.message.edit_text("💠 مشخصات ظاهری رو بنویس:")
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message content is the same, ignore the error
            pass
        else:
            raise e

# async def collect_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     flow_type = user_data.get("flow_type")

#     import logging
#     logging.info(f"Bio handler - User {user_id}: flow_type={flow_type}")

#     # Don't handle if user is in country management flow
#     if flow_type == "country_management":
#         await update.message.reply_text("لطفاً ابتدا از فلوی کشور خارج شوید.")
#         return

#     # Only handle if explicitly in bio flow or has bio-related step
#     if flow_type != "bio" and user_data.get("step") not in ["asking_name", "asking_nickname", "asking_age", "asking_appearance", "asking_history", "asking_id_number", "asking_id_tag", "asking_photo", "selecting_skills"]:
#         await update.message.reply_text("دستور /start رو بزن دوباره.")
#         return

#     text = update.message.text
#     expires_at = user_data.get("expires_at")

#     if expires_at and datetime.utcnow() > datetime.fromisoformat(expires_at):
#         country = user_data["country"]
#         job = user_data["job"]
#         job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)
#         if job_data:
#             job_data["count"] += 1
#             save_data({
#                 "jobs_by_country": jobs_by_country,
#                 "skills_config": skills_config
#             })
#             bios = load_bios()
#             bios["bios"][str(user_id)] = {
#                 "step": "asking_name",   # یا هر مرحله‌ای که در ادامه هست
#                 "country": country_name,
#                 "job": job_name,
#                 "flow_type": "bio"
#             }
#             save_bios(bios)

#         context.user_data.pop(user_id, None)
#         await update.message.reply_text("⏳ مهلت 30 دقیقه‌ات برای تکمیل فرم بیو تموم شد. دوباره /start بزن.")
#         return

#     if user_id not in context.user_data:
#         await update.message.reply_text("دستور /start رو بزن دوباره.")
#         return

#     step = context.user_data[user_id]["step"]
#     current = context.user_data[user_id]

#     next_steps = [
#         ("asking_name", "name", "📛 لقب رو بفرست:"),
#         ("asking_nickname", "nickname", "🎂 سن رو بفرست:"),
#         ("asking_age", "age", None), 
#         ("asking_appearance", "appearance", "📖 سرگذشت کرکترت رو بنویس:"),
#         ("asking_history", "history", "🆔 آیدیت رو وارد کن:"),
#         ("asking_id_number", "id_number", "🔖 هشتگ اختصاصیت رو وارد کن:"),
#         ("asking_id_tag", "user_id_tag", "🖼 حالا یه عکس داف از کرکترت بفرست:"),
#     ]

#     for i, (s, key, msg) in enumerate(next_steps):
#         if step == s:
#             if key:
#                 # Validate age
#                 if key == "age":
#                     if not validate_age(text):
#                         await update.message.reply_text("⚠️ یک عدد صحیح بین 10 تا 100 برای سن بزن.")
#                         return

#                 # Validate hashtag
#                 if key == "user_id_tag":
#                     used_tags = get_used_hashtags()
#                     is_valid, message_or_hashtag = validate_hashtag(text, used_tags)

#                     if not is_valid:
#                         await update.message.reply_text(message_or_hashtag)
#                         return

#                     # Use the formatted hashtag returned by the validation function
#                     text = message_or_hashtag

#                 # Validate username
#                 if key == "id_number":
#                     if not validate_username(text):
#                         await update.message.reply_text("⚠️ ایدیتو درست بزن (مثال: @yourusername).")
#                         return

#                     username = update.message.from_user.username
#                     if not username:
#                         await update.message.reply_text("❌ اکانتت ایدی نداره اول برای اکانتت ایدی بزار بعد بیا.")
#                         return

#                     if text[1:].lower() != username.lower():
#                         await update.message.reply_text(f"❌ آیدی که زدی با ایدی اصلیت فرق داره زرنگ!\n ایدیت : @{username}")
#                         return

#                 current[key] = text

#             next_step = next_steps[i + 1][0] if i + 1 < len(next_steps) else "asking_photo"

#             if next_step == "asking_appearance":
#                 current["skills"] = []
#                 context.user_data[user_id]["step"] = "selecting_skills"
#                 await show_skill_selection(update, context, page=0)
#                 return

#             context.user_data[user_id]["step"] = next_step
#             await update.message.reply_text(msg)
#             return

#     if step == next_steps[-1][0]: 
#         current["user_id_tag"] = text
#         context.user_data[user_id]["step"] = "asking_photo"
#         await update.message.reply_text("🖼 حالا یه عکس داف از کرکترت بفرست:")
#         return

#     if step == "asking_photo":
#         if not update.message.photo:
#             await update.message.reply_text("گفتم یه عکس بفرس.")
#             return

#         photo = update.message.photo[-1].file_id
#         current["photo"] = photo
#         context.user_data[user_id]["step"] = "pending"

#         country = current["country"]
#         job = current["job"]
#         job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)

#         if not job_data:
#             await update.message.reply_text("❌این شغله نیست تو لیست.")
#             return

#         level = job_data["level"]
#         current["level"] = level

#         caption = format_bio_text(current)
#         unique_id = str(update.message.from_user.id)
#         context.user_data[user_id]["unique_id"] = unique_id

#         buttons = bio_approval_keyboard(unique_id)

#         add_bio_to_storage(user_id, current)
#         # Add hashtag to used list
#         add_used_hashtag(current["user_id_tag"])

#         # Remove from job reservations since bio is now submitted
#         reservations = load_job_reservations()
#         if str(user_id) in reservations:
#             del reservations[str(user_id)]
#             save_job_reservations(reservations)

#         await asyncio.gather(*[
#     context.bot.send_photo(
#         chat_id=admin_id,
#         photo=photo,
#         caption=caption,
#         reply_markup=buttons
#     )
#     for admin_id in BIO_ADMIN_ID
# ])

#     await update.message.reply_text("✅ فرم بیوت کامل شد خوشگلشم کردم فرستادم برا ادمین صبر کن زنده شه چکش کنه", reply_markup=restart_button())
#     current.pop("skills_description_sent", None)
#     context.user_data.pop(user_id)

async def collect_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    flow_type = user_data.get("flow_type")

    if flow_type == "country_management":
        await update.message.reply_text("لطفاً ابتدا از فلوی کشور خارج شوید.")
        return

    allowed_steps = ["asking_name", "asking_nickname", "asking_age", "asking_appearance",
                     "asking_history", "asking_id_number", "asking_id_tag", "asking_photo", "selecting_skills"]
    if flow_type != "bio" and user_data.get("step") not in allowed_steps:
        await update.message.reply_text("دستور /start رو بزن دوباره.")
        return

    text = update.message.text.strip() if update.message.text else ""

    expires_at = user_data.get("expires_at")
    if expires_at and datetime.utcnow() > datetime.fromisoformat(expires_at):
        # اینجا همونجا پاک نکن، فقط اجازه بده تابع استارت پاکش کنه
        await update.message.reply_text("⏳ مهلت ۳۰ دقیقه‌ای شما به پایان رسید. لطفا دوباره /start بزنید.")
        context.user_data.pop(user_id, None)
        return

    if user_id not in context.user_data:
        await update.message.reply_text("دستور /start رو بزن دوباره.")
        return

    step = context.user_data[user_id]["step"]
    current = context.user_data[user_id]

    next_steps = [
        ("asking_name", "name", "📛 لطفا لقب شخصیتت رو بفرست:"),
        ("asking_nickname", "nickname", "🎂 لطفا سن شخصیتت رو وارد کن:"),
        ("asking_age", "age", None),
        ("asking_appearance", "appearance", "📖 لطفا سرگذشت شخصیتت رو بنویس:"),
        ("asking_history", "history", "🆔 آیدی شخصیت رو وارد کن:"),
        ("asking_id_number", "id_number", "🔖 هشتگ اختصاصی شخصیت رو وارد کن:"),
        ("asking_id_tag", "user_id_tag", "🖼 لطفا یک عکس از شخصیتت بفرست:")
    ]

    for i, (s, key, msg) in enumerate(next_steps):
        if step == s:
            if key:
                if key == "age":
                    if not validate_age(text):
                        await update.message.reply_text("⚠️ سن باید عددی بین ۱۰ تا ۱۰۰ باشد.")
                        return

                # if key == "user_id_tag":
                    # در مرحله هشتگ: اعتبارسنجی و سپس ذخیره + تغییر مرحله به asking_photo
                    # used_tags = get_used_hashtags()
                    # is_valid, message_or_hashtag = validate_hashtag(text, used_tags)
                    # if not is_valid:
                    #     await update.message.reply_text(message_or_hashtag)
                    #     return
                    # text = message_or_hashtag
                    # current["user_id_tag"] = text

                    # # بارگذاری bios و آپدیت فقط بخش هشتگ و مرحله
                    # bios = load_bios()
                    # bios.setdefault("bios", {})
                    # saved = bios["bios"].get(str(user_id), {})
                    # saved.update(current)
                    # saved["step"] = "asking_photo"  # تغییر مرحله به عکس
                    # saved["saved_at"] = datetime.utcnow().isoformat()
                    # bios["bios"][str(user_id)] = saved
                    # save_bios(bios)

                    used_tags = get_used_hashtags()

# اعتبارسنجی هشتگ با چک حساس به حروف کوچک/بزرگ در تابع validate_hashtag (که قبلاً اصلاح کردیم)
                if key == "user_id_tag":
                    bios = load_bios()
                    bios.setdefault("bios", {})
                    used_tags = bios.get("used_hashtags", [])
                
                    is_valid, message_or_hashtag = validate_hashtag(text, used_tags)
                    if not is_valid:
                        await update.message.reply_text(message_or_hashtag)
                        return
                
                    text = message_or_hashtag
                    current["user_id_tag"] = text
                
                    # اگر هشتگ جدید توی لیست نبود، اضافه‌ش کن
                    if text.lower() not in [tag.lower() for tag in used_tags]:
                        used_tags.append(text)
                        bios["used_hashtags"] = used_tags
                
                    saved = bios["bios"].get(str(user_id), {})
                    saved.update(current)
                    saved["step"] = "asking_photo"
                    saved["saved_at"] = datetime.utcnow().isoformat()
                    bios["bios"][str(user_id)] = saved
                
                    save_bios(bios)
                
                    context.user_data[user_id]["step"] = "asking_photo"
                    await update.message.reply_text("🖼 حالا یه عکس داف از کرکترت بفرست:")
                    return


                if key == "id_number":
                    if not validate_username(text):
                        await update.message.reply_text("⚠️ آیدی را درست وارد کن (مثال: @yourusername).")
                        return
                    username = update.message.from_user.username
                    if not username:
                        await update.message.reply_text("❌ اکانت شما آیدی ندارد. لطفا آیدی بسازید سپس ادامه دهید.")
                        return
                    if text[1:].lower() != username.lower():
                        await update.message.reply_text(f"❌ آیدی وارد شده با آیدی اصلی شما متفاوت است!\nآیدی شما: @{username}")
                        return

                current[key] = text

            next_step = next_steps[i + 1][0] if i + 1 < len(next_steps) else "asking_photo"

            if next_step == "asking_appearance":
                current["skills"] = []
                context.user_data[user_id]["step"] = "selecting_skills"
                await show_skill_selection(update, context, page=0)
                return

            # آپدیت بیو ناقص در اینجا: 
            # ذخیره اطلاعات جدید به bios بدون حذف یا تغییر مرحله به pending
            bios = load_bios()
            bios.setdefault("bios", {})
            saved = bios["bios"].get(str(user_id), {})
            saved.update(current)
            saved["step"] = next_step
            saved["saved_at"] = datetime.utcnow().isoformat()
            bios["bios"][str(user_id)] = saved
            save_bios(bios)

            context.user_data[user_id]["step"] = next_step
            if msg:
                await update.message.reply_text(msg)
            return

    # if step == "asking_photo":
    #     if not update.message.photo:
    #         await update.message.reply_text("⚠️ لطفا فقط عکس ارسال کنید.")
    #         return

    #     photo_file_id = update.message.photo[-1].file_id
    #     current["photo"] = photo_file_id
    #     context.user_data[user_id]["step"] = "pending"

    #     country = current.get("country")
    #     job = current.get("job")
    #     job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job), None)
    #     if not job_data:
    #         await update.message.reply_text("❌ شغل انتخابی شما معتبر نیست.")
    #         return

    #     current["level"] = job_data.get("level")

    #     caption = format_bio_text(current)
    #     unique_id = str(user_id)
    #     context.user_data[user_id]["unique_id"] = unique_id

    #     buttons = bio_approval_keyboard(unique_id)

    #     add_bio_to_storage(user_id, current)
    #     add_used_hashtag(current["user_id_tag"])

    #     # ذخیره نهایی بیو در حالت pending
    #     bios = load_bios()
    #     bios.setdefault("bios", {})
    #     saved = bios["bios"].get(str(user_id), {})
    #     saved.update(current)
    #     saved["step"] = "pending"
    #     saved["saved_at"] = datetime.utcnow().isoformat()
    #     bios["bios"][str(user_id)] = saved
    #     save_bios(bios)

    #     await asyncio.gather(*[
    #         context.bot.send_photo(
    #             chat_id=admin_id,
    #             photo=photo_file_id,
    #             caption=caption,
    #             reply_markup=buttons
    #         )
    #         for admin_id in BIO_ADMIN_ID
    #     ])

    #     await update.message.reply_text("✅ فرم بیو شما کامل شد و ارسال شد برای بررسی ادمین.", reply_markup=restart_button())
    #     context.user_data.pop(user_id, None)
    #     return

    if step == "asking_photo":
        if not update.message.photo:
            await update.message.reply_text("⚠️ لطفاً فقط عکس بفرست، نه متن یا چیز دیگه.")
            return
    
        # ذخیره عکس در لیست
        photo_id = update.message.photo[-1].file_id
        photos = current.get("photos", [])
        photos.append(photo_id)
        current["photos"] = photos
    
        # بررسی محدودیت
        if len(photos) > 5:
            photos.pop()  # آخرین عکس حذف شود
            await update.message.reply_text("🚫 حداکثر می‌تونی ۵ تا عکس بفرستی.")
            return
    
        # نمایش شماره عکس و دکمه تأیید
        photo_num = len(photos)
        text = f"📸 عکس {photo_num} دریافت شد."
        if photo_num < 5:
            text += f"\nمی‌تونی تا {5 - photo_num} عکس دیگه بفرستی یا دکمه زیر رو بزن برای ارسال نهایی."
    
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تأیید و ارسال نهایی", callback_data="confirm_bio_photos")]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)
        context.user_data[user_id] = current
        return

    await update.message.reply_text("خطا در فرایند. لطفا /start بزنید و دوباره شروع کنید.")

async def confirm_bio_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    current = context.user_data.get(user_id, {})

    photos = current.get("photos", [])
    if not photos:
        await query.edit_message_text("❌ هنوز هیچ عکسی نفرستادی!")
        return

    country = current.get("country")
    job = current.get("job")
    job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job), None)
    if not job_data:
        await query.edit_message_text("❌ شغل انتخابی شما معتبر نیست.")
        return

    current["level"] = job_data.get("level")
    caption = format_bio_text(current)
    unique_id = str(user_id)
    current["unique_id"] = unique_id
    buttons = bio_approval_keyboard(unique_id)

    # پیام وضعیت
    await query.edit_message_text("📤 در حال ارسال بیو به ادمین‌ها...")

    # ساخت گروه مدیا
    media_group = []
    for i, photo_id in enumerate(photos):
        # فقط عکس اول کپشن دارد
        media_group.append(
            InputMediaPhoto(
                media=photo_id,
                caption=caption if i == 0 else "",
                parse_mode="HTML"
            )
        )

    # ارسال به ادمین‌ها با کنترل خطا
    sent_success = False
    for admin_id in BIO_ADMIN_ID:
        try:
            messages = await context.bot.send_media_group(
                chat_id=admin_id,
                media=media_group
            )
            # اضافه کردن دکمه زیر پیام اول
            if messages:
                first_message = messages[0]
                await context.bot.edit_message_reply_markup(
                    chat_id=admin_id,
                    message_id=first_message.message_id,
                    reply_markup=buttons
                )
                sent_success = True
            await asyncio.sleep(1.5)  # جلوگیری از Flood
        except Exception as e:
            print(f"⚠️ Error sending to admin {admin_id}: {e}")

    if not sent_success:
        await query.edit_message_text("❌ ارسال به ادمین‌ها انجام نشد. لطفاً بعداً دوباره تلاش کنید.")
        return

    # ذخیره بیو و اطلاعات
    add_bio_to_storage(user_id, current)
    add_used_hashtag(current["user_id_tag"])

    bios = load_bios()
    bios.setdefault("bios", {})
    saved = bios["bios"].get(str(user_id), {})
    saved.update(current)
    saved["step"] = "pending"
    saved["saved_at"] = datetime.utcnow().isoformat()
    bios["bios"][str(user_id)] = saved
    save_bios(bios)

    reservations = load_job_reservations()
    if str(user_id) in reservations:
        del reservations[str(user_id)]
        save_job_reservations(reservations)

    await query.message.reply_text(
        "✅ فرم بیوت کامل شد و برای بررسی ادمین ارسال شد.",
        reply_markup=restart_button()
    )
    context.user_data.pop(user_id, None)

