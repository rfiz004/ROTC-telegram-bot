from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import json
import os
from keep_alive import keep_alive



DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"jobs_by_country": {}, "skills_list": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# استفاده از داده‌ها
data = load_data()
jobs_by_country = data["jobs_by_country"]
skills_list = data["skills_list"]


BOT_TOKEN = os.environ["BOT_TOKEN"]
BIO_ADMIN_ID = 5890943003
BIO_CHANNEL = "@R_O_T_C_Bio"

user_state = {}

countries = ["Aldemar", "Alpyr", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]


rp_passwords = {
    "main_admin": os.environ["MAIN_ADMIN_PASS"],
    "bio_admin": os.environ["BIO_ADMIN_PASS"],
    "shop_admin": os.environ["SHOP_ADMIN_PASS"]
}

# دکمه‌های مشترک

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")]])

def restart_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔁 شروع مجدد", callback_data="back_to_main")]])

def bio_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 لیست مشاغل", callback_data="admin_job_list")],
        [InlineKeyboardButton("📚 لیست مهارت‌ها", callback_data="admin_skill_list")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")]
    ])

def country_selection_keyboard(prefix):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"کشور {c}", callback_data=f"{prefix}_{c}")] for c in countries] +
        [[InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]]
    )

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 👋\nمیخوای چیکار بکنی؟", reply_markup=main_menu)

main_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("📜 تحویل بیو", callback_data="bio")],
    [InlineKeyboardButton("🏰 مدیریت کشور", callback_data="manage_country")],
    [InlineKeyboardButton("⚙️ تنظیمات آرپی", callback_data="rp_settings")],
    [InlineKeyboardButton("📢 چنل‌های آرپی", callback_data="rp_channels")]
])

# رمز ورود برای ادمین‌ها
async def handle_password_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = user_state.get(user_id, {})

    if state.get("step") == "awaiting_rp_password":
        if text == rp_passwords["main_admin"]:
            await update.message.reply_text("🎛 خوش اومدی ادمین اصلی!")
        elif text == rp_passwords["bio_admin"]:
            await update.message.reply_text("🧾 به پنل ادمین بیو خوش اومدی!", reply_markup=bio_admin_menu())
        elif text == rp_passwords["shop_admin"]:
            await update.message.reply_text("🛍 به پنل ادمین شاپ خوش اومدی!")
        else:
            await update.message.reply_text("❌ رمز اشتباهه.")
        user_state.pop(user_id)

# منو اصلی
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "bio":
        await select_country(update, context)
    elif data == "manage_country":
        await query.message.edit_text("این بخش بعداً اضافه می‌شه 🏗", reply_markup=back_button())
    elif data == "rp_settings":
        await query.message.edit_text("🔐 لطفاً رمز ورود به تنظیمات رو بفرست:")
        user_state[query.from_user.id] = {"step": "awaiting_rp_password"}
    elif data == "rp_channels":
        await query.message.edit_text("📢 چنل‌ها: \n@R_O_T_C_Bio", reply_markup=back_button())
    elif data == "back_to_main":
        await query.message.edit_text("سلام! 👋\nمیخوای چیکار بکنی؟", reply_markup=main_menu)
    elif data == "back_to_admin_menu":
        await query.message.edit_text("🧾 به پنل ادمین بیو خوش اومدی!", reply_markup=bio_admin_menu())
    elif data == "admin_job_list":
        await query.message.edit_text("🌍 انتخاب کشور برای مدیریت مشاغل:", reply_markup=country_selection_keyboard("manage_jobs"))
    elif data == "admin_skill_list":
        skills_text = "📚 لیست مهارت‌ها:\n" + "\n".join(f"🔹 {s}" for s in skills_list)
        await query.message.edit_text(skills_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ افزودن مهارت", callback_data="add_skill")],
            [InlineKeyboardButton("➖ حذف مهارت", callback_data="remove_skill")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]
        ]))
    elif data == "add_skill":
        await query.message.edit_text("📝 مهارت جدید رو بنویس:")
        user_state[query.from_user.id] = {"step": "adding_skill"}
    elif data == "remove_skill":
        await query.message.edit_text("🗑 اسم مهارتی که می‌خوای حذف کنی رو بنویس:")
        user_state[query.from_user.id] = {"step": "removing_skill"}

# بیوگرافی
async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = {"step": "selecting_country"}

    keyboard = [[InlineKeyboardButton(f"کشور {c}", callback_data=f"select_country_{c}")] for c in countries]
    keyboard.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    await query.message.edit_text("برای کدوم کشور می‌خوای بیو بدی؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def select_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    country = query.data.split("_")[2]
    user_state[user_id] = {"step": "selecting_job", "country": country}

    job_buttons = []
    job_text = "👥 مشاغل موجود:\n"
    for job in jobs_by_country[country]:
        if job["count"] > 0:
            job_buttons.append([InlineKeyboardButton(f"{job['name']} (لول {job['level']})", callback_data=f"job_{job['name']}")])
            job_text += f"🔹 {job['name']} - لول: {job['level']} - ظرفیت: {job['count']} نفر\n"
    job_buttons.append([InlineKeyboardButton("🔙 برگشت", callback_data="back_to_main")])
    await query.message.edit_text(job_text, reply_markup=InlineKeyboardMarkup(job_buttons))

async def ask_bio_fields(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    job = query.data[4:]
    user_state[user_id]["job"] = job
    user_state[user_id]["step"] = "asking_name"
    await query.message.edit_text("✍️ اسم شخصیت رو وارد کن:")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_state.get(user_id, {})
    step = state.get("step")

    if state.get("step") == "awaiting_rp_password":
        await handle_password_message(update, context)
    elif state.get("step") == "adding_skill":
        skills_list.append(update.message.text)
        save_data({
             "jobs_by_country": jobs_by_country,
             "skills_list": skills_list
        })
        await update.message.reply_text("✅ مهارت اضافه شد.", reply_markup=bio_admin_menu())
        user_state.pop(user_id)
    elif state.get("step") == "removing_skill":
        skill_to_remove = update.message.text
        if skill_to_remove in skills_list:
            skills_list.remove(skill_to_remove)
            save_data({
              "jobs_by_country": jobs_by_country,
              "skills_list": skills_list
            })
            await update.message.reply_text("❌ مهارت حذف شد.", reply_markup=bio_admin_menu())
        else:
            await update.message.reply_text("⚠️ مهارت پیدا نشد.", reply_markup=bio_admin_menu())
        user_state.pop(user_id)
    elif step == "add_job":
        try:
            name, level, count = [x.strip() for x in update.message.text.split("-")]
            level = int(level)
            count = int(count)
            country = state["country"]
            jobs_by_country[country].append({"name": name, "level": level, "count": count})
            save_data({
                "jobs_by_country": jobs_by_country,
                "skills_list": skills_list
            })
            await update.message.reply_text("✅ شغل اضافه شد.", reply_markup=bio_admin_menu())
        except:
            await update.message.reply_text("❌ فرمت نادرست بود.")
        user_state.pop(user_id)

    elif step == "remove_job":
        name = update.message.text.strip()
        country = state["country"]
        jobs = jobs_by_country[country]
        jobs_by_country[country] = [j for j in jobs if j["name"] != name]
        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_list": skills_list
        })
        await update.message.reply_text("❌ شغل حذف شد.", reply_markup=bio_admin_menu())
        user_state.pop(user_id)

    elif step == "increase_job":
        try:
            name, amount = [x.strip() for x in update.message.text.split("-")]
            amount = int(amount)
            country = state["country"]
            job = next(j for j in jobs_by_country[country] if j["name"] == name)
            job["count"] += amount
            save_data({
              "jobs_by_country": jobs_by_country,
              "skills_list": skills_list
            })
            await update.message.reply_text("✅ ظرفیت افزایش یافت.", reply_markup=bio_admin_menu())
        except:
            await update.message.reply_text("❌ خطا در افزایش ظرفیت.")
        user_state.pop(user_id)

    elif step == "decrease_job":
        try:
            name, amount = [x.strip() for x in update.message.text.split("-")]
            amount = int(amount)
            country = state["country"]
            job = next(j for j in jobs_by_country[country] if j["name"] == name)
            job["count"] = max(0, job["count"] - amount)
            await update.message.reply_text("✅ ظرفیت کاهش یافت.", reply_markup=bio_admin_menu())
        except:
            await update.message.reply_text("❌ خطا در کاهش ظرفیت.")
        user_state.pop(user_id)
    else:
        await collect_bio(update, context)

async def collect_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_state:
        await update.message.reply_text("دستور /start رو بزن دوباره.")
        return

    step = user_state[user_id]["step"]
    current = user_state[user_id]

    next_steps = [
        ("asking_name", "name", "📛 لقب رو بفرست:"),
        ("asking_nickname", "nickname", "🎂 سن رو بفرست:"),
        ("asking_age", "age", "🔧 مهارت‌هات رو یکی‌یکی وارد کن (سه‌تا):\n📝 لیست مهارت‌ها: " + ", ".join(skills_list)),
        ("asking_skill1", "skill1", "مهارت دوم:"),
        ("asking_skill2", "skill2", "مهارت سوم:"),
        ("asking_skill3", "skill3", "💠 مشخصات ظاهری رو بنویس:"),
        ("asking_appearance", "appearance", "📖 سرگذشت شخصیت رو بنویس:"),
        ("asking_history", "history", "🆔 آیدیت رو وارد کن:"),
        ("asking_id_number", "id_number", "🔖 هشتگ اختصاصی رو وارد کن:"),
        ("asking_id_tag", "user_id_tag", "🖼 حالا یک عکس از شخصیت بفرست:")
    ]

    for i, (s, key, msg) in enumerate(next_steps):
        if step == s:
            current[key] = text
            user_state[user_id]["step"] = next_steps[i + 1][0] if i + 1 < len(next_steps) else "asking_photo"
            await update.message.reply_text(msg)
            return

    if step == "asking_photo":
        if not update.message.photo:
            await update.message.reply_text("لطفاً یک عکس بفرست.")
            return

        photo = update.message.photo[-1].file_id
        current["photo"] = photo

        country = current["country"]
        job = current["job"]
        job_data = next((j for j in jobs_by_country[country] if j["name"] == job), None)

        if not job_data:
            await update.message.reply_text("❌ شغل نامعتبر است.")
            return

        level = job_data["level"]
        current["level"] = level
        job_data["count"] -= 1
        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_list": skills_list
        })


        bio_text = (
            f"── ⃟ ⃟─⊳𝗕𝗶𝗼𝗴𝗿𝗮𝗽𝗵𝘆 ──╰𝗟𝗲𝘃𝗲𝗹 /\n"
            f"─ 𝗡𝗮𝗺𝗲 ─⊳ {current['name']}\n"
            f"─ 𝗡𝗶𝗰𝗸𝗻𝗮𝗺𝗲 ─⊳ {current['nickname']}\n"
            f"─ 𝗔𝗴𝗲 ─⊳ {current['age']}\n"
            f"─ 𝗝𝗼𝗯 ─⊳ {job}\n"
            f"─ Countries ─⊳ کشور {country}\n"
            f"─ Skills ─⊳ {current['skill1']}, {current['skill2']}, {current['skill3']}\n"
            f"─ Level ─⊳ {level}\n"
            f"─ 𝗔𝗽𝗽𝗲𝗮𝗿𝗮𝗻𝗰𝗲 ─⊳ {current['appearance']}\n"
            f"─ 𝗛𝗶𝘀𝘁𝗼𝗿𝘆 ─⊳ {current['history']}\n"
            f"─ 𝗜𝗗 ─⊳ {current['id_number']} | {current['user_id_tag']}\n───────────  ⃟ ⃟─⊳ \n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
        )

        caption = bio_text + "\n\n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
        await context.bot.send_photo(chat_id=BIO_ADMIN_ID, photo=photo, caption=caption)
        await update.message.reply_text("✅ فرم بیو با موفقیت ارسال شد برای بررسی ادمین.", reply_markup=restart_button())
        user_state.pop(user_id)


async def show_country_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    country = data.split("_")[2]

    jobs = jobs_by_country.get(country)
    if not jobs:
        await query.message.edit_text("❌ کشور یافت نشد.", reply_markup=back_button())
        return

    text = f"👥 لیست مشاغل در کشور {country}:\n"
    for job in jobs:
        text += f"🔹 {job['name']} - لول: {job['level']} - ظرفیت باقی‌مانده: {job['count']}\n"

    job_buttons = [
        [InlineKeyboardButton("➕ افزودن شغل", callback_data=f"add_job_{country}")],
        [InlineKeyboardButton("❌ حذف شغل", callback_data=f"remove_job_{country}")],
        [InlineKeyboardButton("🔼 افزایش ظرفیت", callback_data=f"increase_job_{country}")],
        [InlineKeyboardButton("🔽 کاهش ظرفیت", callback_data=f"decrease_job_{country}")],
        [InlineKeyboardButton("🔙 برگشت", callback_data="back_to_admin_menu")]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(job_buttons))

async def handle_job_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    action, country = data.split("_job_")

    user_state[user_id] = {"step": f"{action}_job", "country": country}

    if action == "add":
        await query.message.edit_text("📝 فرمت افزودن شغل:\nنام شغل - لول - ظرفیت\nمثال: شکارچی - 2 - 3")
    elif action == "remove":
        await query.message.edit_text("❌ نام شغلی که می‌خوای حذف کنی رو بنویس:")
    elif action == "increase":
        await query.message.edit_text("🔼 بنویس: نام شغل - تعداد افزایش\nمثال: دکتر - 2")
    elif action == "decrease":
        await query.message.edit_text("🔽 بنویس: نام شغل - تعداد کاهش\nمثال: دکتر - 1")
    else:
        await query.message.edit_text("❌ شغل موردنظر پیدا نشد یا حذف شده است.")




# راه‌اندازی ربات
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(select_job, pattern="^select_country_"))
app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^job_"))
app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
app.add_handler(CallbackQueryHandler(handle_main_menu))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_all_messages))
app.add_handler(MessageHandler(filters.PHOTO, collect_bio))

print("🤖 ربات در حال اجراست...")
keep_alive()
app.run_polling()
