
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# from datetime import datetime, timedelta
from datetime import datetime, timezone, timedelta
import re
from data_manager import jobs_by_country, skills_list, save_data, add_bio_to_storage
from keyboards import country_jobs_keyboard, create_skill_selection_keyboard, bio_approval_keyboard, restart_button
from utils import calculate_skill_pages, get_page_skills, validate_age, validate_hashtag, validate_username, format_bio_text, is_hashtag_unique_permanent, save_used_hashtag
from config import BIO_ADMIN_ID, SKILLS_PER_PAGE, COUNTRIES

async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    context.user_data[user_id] = {"step": "selecting_country"}
    await query.message.edit_text("برای کدوم کشور می‌خوای بیو بدی؟", reply_markup=country_jobs_keyboard())

async def select_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    country = query.data.split("_")[2]
    context.user_data[user_id] = {"step": "selecting_job", "country": country}

    job_buttons = []
    job_text = "👥 مشاغلی که داریم:\n"
    for job in jobs_by_country[country]:
        if job["count"] > 0:
            job_buttons.append([InlineKeyboardButton(f"{job['name']} (لول {job['level']})", callback_data=f"job_{job['name']}")])
            job_text += f"🔹 {job['name']} - لول: {job['level']} - ظرفیت: {job['count']} نفر\n"
    job_buttons.append([InlineKeyboardButton("🔙 برگشتن", callback_data="back_to_main")])
    await query.message.edit_text(job_text, reply_markup=InlineKeyboardMarkup(job_buttons))

async def ask_bio_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    job = query.data[4:]  # Remove "job_" prefix
    country = context.user_data[user_id]["country"]

    context.user_data[user_id]["job"] = job

    job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)
    if job_data:
        job_data["count"] = max(0, job_data["count"] - 1)

        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_list": skills_list
        })

        # Set expiration time and step
        context.user_data[user_id]["expires_at"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        context.user_data[user_id]["step"] = "asking_name"

        # Send separate messages
        await query.message.reply_text("⏳ از این لحظه 30 دقیقه فرصت داری فرم بیوت رو کامل کنی. اگر دیر بجنبی شغل رزرو شده آزاد میشه!")
        await query.message.reply_text("📛بچه خوشگل اسم کارکترتو کخ کن بیاد")
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

    current = context.user_data[user_id]
    selected = current.get("skills", [])
    total_pages = calculate_skill_pages(skills_list)

    context.user_data[user_id]["skill_page"] = page

    # Skills for this page
    page_skills = get_page_skills(skills_list, page)

    # Store skills by page in context
    if 'skills_by_page' not in context.user_data:
        context.user_data['skills_by_page'] = {}
    context.user_data['skills_by_page'][page] = page_skills

    # Create keyboard
    keyboard = create_skill_selection_keyboard(page_skills, selected, page, total_pages)

    # Text
    skill_text = "🔧 مهارت‌هات رو انتخاب کن (حداکثر ۳):\n"
    if selected:
        skill_text += "\n✅ انتخاب‌شده‌ها:\n" + "\n".join(f"🔹 {s}" for s in selected)
    else:
        skill_text += "\n⚠️ فعلاً مهارتی انتخاب نشده."

    # Send or edit message
    if update.callback_query:
        await query.message.edit_text(skill_text, reply_markup=keyboard)
    else:
        await update.message.reply_text(skill_text, reply_markup=keyboard)

async def handle_skill_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    match = re.match(r"select_skill_(\d+)_(\d+)", query.data)
    if not match:
        return  
    page_str, index_str = match.groups()
    page = int(page_str)
    index = int(index_str)
    
    skills_by_page = context.user_data.get("skills_by_page", {})
    page_skills = skills_by_page.get(page, [])

    if index >= len(page_skills):
        await query.answer("❌ خطا در انتخاب مهارت.")
        return

    skill = page_skills[index]
    state = context.user_data.get(user_id, {})
    selected = state.get("skills", [])

    if skill in selected:
        await query.answer("⚠️ این مهارت رو قبلاً انتخاب کردی!", show_alert=True)
        return

    if len(selected) >= 3:
        await query.answer("⚠️ فقط ۳ مهارت می‌تونی انتخاب کنی!", show_alert=True)
        return

    # Save selection but don't move to next step
    selected.append(skill)
    state["skills"] = selected
    if len(selected) == 3:
        state["skill1"], state["skill2"], state["skill3"] = selected
    await show_skill_selection(update, context, page=state.get("skill_page", 0))

async def handle_skill_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" not in str(e):
            raise
    user_id = query.from_user.id
    page = int(query.data.split("_")[-1])
    context.user_data[user_id]["skill_page"] = page
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
    await query.answer()
    user_id = query.from_user.id
    state = context.user_data.get(user_id, {})

    if len(state.get("skills", [])) < 3:
        await query.answer("⚠️ هنوز ۳ مهارت انتخاب نکردی.", show_alert=True)
        return

    state["step"] = "asking_appearance"
    await query.message.edit_text("💠 مشخصات ظاهری رو بنویس:")

async def collect_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id


    
    text = update.message.text

    user_data = context.user_data.get(user_id, {})
    expires_at = user_data.get("expires_at")
    
    if expires_at and datetime.now(timezone.utc) > datetime.fromisoformat(expires_at):
        country = user_data["country"]
        job = user_data["job"]
        job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)
        if job_data:
            job_data["count"] += 1
            save_data({
                "jobs_by_country": jobs_by_country,
                "skills_list": skills_list
            })
        context.user_data.pop(user_id, None)
        await update.message.reply_text("⏳ مهلت 30 دقیقه‌ات برای تکمیل فرم بیو تموم شد. دوباره /start بزن.")
        return

    if user_id not in context.user_data:
        await update.message.reply_text("دستور /start رو بزن دوباره.")
        return

    step = context.user_data[user_id]["step"]
    current = context.user_data[user_id]

    next_steps = [
        ("asking_name", "name", "📛 لقب رو بفرست:"),
        ("asking_nickname", "nickname", "🎂 سن رو بفرست:"),
        ("asking_age", "age", None), 
        ("asking_appearance", "appearance", "📖 سرگذشت کرکترت رو بنویس:"),
        ("asking_history", "history", "🆔 آیدیت رو وارد کن:"),
        ("asking_id_number", "id_number", "🔖 هشتگ اختصاصیت رو وارد کن:"),
        ("asking_id_tag", "user_id_tag", "🖼 حالا یه عکس داف از کرکترت بفرست:"),
    ]

    for i, (s, key, msg) in enumerate(next_steps):
        if step == s:
            if key:
                # Validate age
                if key == "age":
                    if not validate_age(text):
                        await update.message.reply_text("⚠️ یک عدد صحیح بین 10 تا 100 برای سن بزن.")
                        return

                # Validate hashtag
                if key == "user_id_tag":
                    if not validate_hashtag(text):
                        await update.message.reply_text("⚠️ هشتگ رو با # شروع کن و فقط حروف یا عدد بعدش بیار (بدون فاصله).")
                        return
                    if not is_hashtag_unique_permanent(text):
                        await update.message.reply_text("⚠️ این هشتگ قبلاً استفاده شده. یکی دیگه بزن.")
                        return
                    save_used_hashtag(text)

                # Validate username
                if key == "id_number":
                    if not validate_username(text):
                        await update.message.reply_text("⚠️ ایدیتو درست بزن (مثال: @yourusername).")
                        return

                    username = update.message.from_user.username
                    if not username:
                        await update.message.reply_text("❌ اکانتت ایدی نداره اول برای اکانتت ایدی بزار بعد بیا.")
                        return

                    if text[1:].lower() != username.lower():
                        await update.message.reply_text(f"❌ آیدی که زدی با ایدی اصلیت فرق داره زرنگ!\n ایدیت : @{username}")
                        return

                current[key] = text

            next_step = next_steps[i + 1][0] if i + 1 < len(next_steps) else "asking_photo"

            if next_step == "asking_appearance":
                current["skills"] = []
                context.user_data[user_id]["step"] = "selecting_skills"
                await show_skill_selection(update, context, page=0)
                return

            context.user_data[user_id]["step"] = next_step
            await update.message.reply_text(msg)
            return

    if step == next_steps[-1][0]: 
        current["user_id_tag"] = text
        context.user_data[user_id]["step"] = "asking_photo"
        await update.message.reply_text("🖼 حالا یه عکس داف از کرکترت بفرست:")
        return

    if step == "asking_photo":
        if not update.message.photo:
            await update.message.reply_text("گفتم یه عکس بفرس.")
            return

        photo = update.message.photo[-1].file_id
        current["photo"] = photo

        country = current["country"]
        job = current["job"]
        job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)

        if not job_data:
            await update.message.reply_text("❌این شغله نیست تو لیست.")
            return

        level = job_data["level"]
        current["level"] = level
        
        current["step"] = "completed"
      
        caption = format_bio_text(current)
        unique_id = str(update.message.from_user.id)
        context.user_data[user_id]["unique_id"] = unique_id

        buttons = bio_approval_keyboard(unique_id)

        

        add_bio_to_storage(user_id, current)

        await context.bot.send_photo(
            chat_id=BIO_ADMIN_ID,
            photo=photo,
            caption=caption,
            reply_markup=buttons
        )
        await update.message.reply_text("✅ فرم بیوت کامل شد خوشگلشم کردم فرستادم برا ادمین صبر کن زنده شه چکش کنه", reply_markup=restart_button())
        context.user_data.pop(user_id)

