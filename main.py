from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import json
from uuid import uuid4
from telegram.constants import ChatType
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from keep_alive import keep_alive
import re
import asyncio
import os
from telegram.ext import ApplicationBuilder
from telegram.ext import Application
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 8443))

SKILLS_PER_PAGE = 12

pv_filter = filters.ChatType.PRIVATE

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


BIO_ADMIN_ID = 5890943003
BIO_CHANNEL = "@R_O_T_C_Bio"

user_state = {}

countries = ["Aldemar", "Alpyr", "Walden", "Northwood", "Santos", "Imperial", "Azure", "Hikada", "Alestria"]


rp_passwords = {
    "main_admin": "amirbitch",
    "bio_admin": "biobio",
    "shop_admin": "shopshop"
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
            await update.message.reply_text("ها چیه چی میخواستی باشه؟؟")
        elif text == rp_passwords["bio_admin"]:
            await update.message.reply_text("خوش اومدی سیسی کیوت (امیر و علی اگه اومدن گمشن)", reply_markup=bio_admin_menu())
        elif text == rp_passwords["shop_admin"]:
            await update.message.reply_text("اینجا فعلا صاحاب نداره")
        else:
            await update.message.reply_text("ادمین اصلیا عین ادم بزنین، سیسیا قشنگام اگه یادتون نیست بیاین بگم بهتون، غیر ادمینام (و ادمین اصلیا) گمشن ممنون")
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
        await query.message.edit_text(
            "📢 چنل‌ها:\n\n" 
            "🔷 <a href='https://t.me/R_O_T_C'>کانال اصلی</a>\n\n"
            "🧬 <a href='https://t.me/R_O_T_C_Bio'>کانال بیوگرافی شخصیت‌ها</a>\n\n"
            "📰 <a href='https://t.me/R_O_T_C_News'>اخبار و اطلاعیه‌های رول</a>\n\n"
            "🎭 <a href='https://t.me/R_O_T_C_Memes'>میم‌ها و لحظات فان</a>\n\n"
            "🛒 <a href='https://t.me/R_O_T_C_Shop'>شاپ و فروشگاه رول</a>\n\n",
            reply_markup=back_button(),
            parse_mode="HTML"
        )
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
    await query.message.edit_text("بچه خوشگل اسم کارکترتو کخ کن بیاد🥰‌")

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_state.get(user_id, {})
    step = state.get("step")

    if state.get("step") == "awaiting_rp_password":
        await handle_password_message(update, context)
    elif state.get("step") == "adding_skill":
        skill = update.message.text.strip()

        if skill in skills_list:
            await update.message.reply_text("⚠️ این مهارت قبلاً وجود داره.", reply_markup=bio_admin_menu())
        else:
            skills_list.append(skill)
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
        parts = update.message.text.split("-")
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت اشتباهه.")
            return
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
        
    elif state.get("reject_step") == "awaiting_text":
        for uid, d in context.chat_data.items():
            if d.get("user_id") == user_id and d.get("reject_step") == "awaiting_text":
                d["rejection_reason"] = update.message.text
                d["reject_step"] = "ready"
                await update.message.reply_text("✏️ متن ذخیره شد. حالا از دکمه‌ها استفاده کن.")
                return

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
            ("asking_age", "age", None), 
            ("asking_appearance", "appearance", "📖 سرگذشت شخصیت رو بنویس:"),
            ("asking_history", "history", "🆔 آیدیت رو وارد کن:"),
            ("asking_id_number", "id_number", "🔖 هشتگ اختصاصی رو وارد کن:"),
            ("asking_id_tag", "user_id_tag", "🖼 حالا یه عکس از شخصیتت بفرست:"),
        ]


    for i, (s, key, msg) in enumerate(next_steps):
        if step == s:
            if key:
                # بررسی سن
                if key == "age":
                    if not text.isdigit() or not (10 <= int(text) <= 100):
                        await update.message.reply_text("⚠️ یک عدد صحیح بین 10 تا 100 برای سن بزن.")
                        return

                # بررسی هشتگ اختصاصی
                if key == "user_id_tag":
                    if not text.startswith("#") or not text[1:].isalnum():
                        await update.message.reply_text("⚠️ هشتگ رو با # شروع کن و فقط حروف یا عدد بعدش بیار (بدون فاصله).")
                        return

                # بررسی آیدی @user
                if key == "id_number":
                    if not re.match(r"^@[\w\d_]{5,}$", text):
                        await update.message.reply_text("⚠️ ایدیتو درست بزن (مثال: @yourusername).")
                        return

                    username = update.message.from_user.username
                    if not username:
                        await update.message.reply_text("❌ اکانتت ایدی نداره اول برای اکانتت ایدی بزار بعد بیا.")
                        return

                    if text[1:].lower() != username.lower():
                        await update.message.reply_text(f"❌ آیدی که زدی با ایدی اصلیت فرق داره زرنگ!\nآیدی شما: @{username}")
                        return

                current[key] = text


            next_step = next_steps[i + 1][0] if i + 1 < len(next_steps) else "asking_photo"

            if next_step == "asking_appearance":  # قبلش مرحله مهارت هست
                # بعد از age برو به مرحله انتخاب مهارت
                current["skills"] = []
                user_state[user_id]["step"] = "selecting_skills"
                await show_skill_selection(update, context, page=0)
                return

            user_state[user_id]["step"] = next_step
            await update.message.reply_text(msg)
            return

    if step == next_steps[-1][0]:  # یعنی مرحله آخر بود (asking_id_tag)
        current["user_id_tag"] = text
        user_state[user_id]["step"] = "asking_photo"
        await update.message.reply_text("🖼 حالا یه عکس از شخصیتت بفرست:")
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
            await update.message.reply_text("❌ شغل نامعتبره.")
            return

        level = job_data["level"]
        current["level"] = level

        bio_text = (
            f"── ⃟ ⃟─⊳𝗕𝗶𝗼𝗴𝗿𝗮𝗽𝗵𝘆 ──╰𝗟𝗲𝘃𝗲𝗹 /\n"
            f"─ 𝗡𝗮𝗺𝗲 ─⊳ {current['name']}\n"
            f"─ 𝗡𝗶𝗰𝗸𝗻𝗮𝗺𝗲 ─⊳ {current['nickname']}\n"
            f"─ 𝗔𝗴𝗲 ─⊳ {current['age']}\n"
            f"─ 𝗝𝗼𝗯 ─⊳ {job}\n"
            f"─ Countries ─⊳ کشور {country}\n"
            f"─ Skills ─⊳ {', '.join(current.get('skills', []))}\n"
            f"─ Level ─⊳ {level}\n"
            f"─ 𝗔𝗽𝗽𝗲𝗮𝗿𝗮𝗻𝗰𝗲 ─⊳ {current['appearance']}\n"
            f"─ 𝗛𝗶𝘀𝘁𝗼𝗿𝘆 ─⊳ {current['history']}\n"
            f"─ 𝗜𝗗 ─⊳ {current['id_number']} | {current['user_id_tag']}\n───────────  ⃟ ⃟─⊳ \n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
        )
        caption = bio_text
        unique_id = str(uuid4())
        user_state[user_id]["unique_id"] = unique_id
        context.chat_data[unique_id] = {
            "user_id": user_id,
            "bio_data": current
        }

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"approve_bio_{unique_id}"),
                InlineKeyboardButton("❌ رد", callback_data=f"reject_bio_{unique_id}")
            ]
        ])

        await context.bot.send_photo(
            chat_id=BIO_ADMIN_ID,
            photo=photo,
            caption=caption,
            reply_markup=buttons
        )
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

async def handle_bio_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, _, unique_id = query.data.partition("_bio_")

    data = context.chat_data.get(unique_id)
    if not data:
        await query.message.edit_caption(caption="❌ اطلاعات فرم پیدا نشد یا قبلاً بررسی شده.")
        return

    user_id = data["user_id"]
    bio_data = data["bio_data"]
    photo = bio_data["photo"]

    caption = (
        f"── ⃟ ⃟─⊳𝗕𝗶𝗼𝗴𝗿𝗮𝗽𝗵𝘆 ──╰𝗟𝗲𝘃𝗲𝗹 /\n"
        f"─ 𝗡𝗮𝗺𝗲 ─⊳ {bio_data['name']}\n"
        f"─ 𝗡𝗶𝗰𝗸𝗻𝗮𝗺𝗲 ─⊳ {bio_data['nickname']}\n"
        f"─ 𝗔𝗴𝗲 ─⊳ {bio_data['age']}\n"
        f"─ 𝗝𝗼𝗯 ─⊳ {bio_data['job']}\n"
        f"─ Countries ─⊳ کشور {bio_data['country']}\n"
        f"─ Skills ─⊳ {', '.join(bio_data.get('skills', []))}\n"
        f"─ Level ─⊳ {bio_data['level']}\n"
        f"─ 𝗔𝗽𝗽𝗲𝗮𝗿𝗮𝗻𝗰𝗲 ─⊳ {bio_data['appearance']}\n"
        f"─ 𝗛𝗶𝘀𝘁𝗼𝗿𝘆 ─⊳ {bio_data['history']}\n"
        f"─ 𝗜𝗗 ─⊳ {bio_data['id_number']} | {bio_data['user_id_tag']}\n───────────  ⃟ ⃟─⊳ \n#Bio_form • https://t.me/R_O_T_C\nhttps://t.me/R_O_T_C_Bio"
    )

    if action == "approve":
        country = bio_data["country"]
        job_name = bio_data["job"]
        job_data = next((j for j in jobs_by_country[country] if j["name"] == job_name), None)
        if job_data:
            job_data["count"] = max(0, job_data["count"] - 1)

        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_list": skills_list
        })
        # ارسال به چنل بیو
        await context.bot.send_photo(chat_id=BIO_CHANNEL, photo=photo, caption=caption)

        # ارسال پیام تایید به کاربر
        await context.bot.send_message(chat_id=user_id, text="✅ فرم بیو شما تایید شد و در چنل منتشر شد.")

        # ساخت لینک دعوت یک‌بار مصرف
<<<<<<< HEAD
       # ساخت لینک دعوت یک‌بار مصرف
rol_link = None
realchat_link = None
=======
        # ساخت لینک دعوت یک‌بار مصرف
        rol_link = None
        realchat_link = None
>>>>>>> 441097b (new update(0.5))

try:
    invite_rol = await context.bot.create_chat_invite_link(
        chat_id=-1002616064737,  # 👈 آیدی گپ رول
        member_limit=1,
        creates_join_request=False
    )
    rol_link = invite_rol.invite_link
except Exception as e:
    print(f"❌ خطا در ساخت لینک گپ رول: {e}")

try:
    invite_realchat = await context.bot.create_chat_invite_link(
        chat_id=-1002893489105,  # 👈 آیدی گپ ریل‌چت
        member_limit=1,
        creates_join_request=False
    )
    realchat_link = invite_realchat.invite_link
except Exception as e:
    print(f"❌ خطا در ساخت لینک گپ ریل‌چت: {e}")

# پیام نهایی به کاربر
msg = "📩 لینک‌های ورود به گروه‌ها:\n"
if rol_link:
    msg += f"🔷 گپ رول: {rol_link}\n"
else:
    msg += "⚠️ لینک گپ رول در دسترس نیست.\n"

if realchat_link:
    msg += f"🔸 گپ ریل‌چت: {realchat_link}"
else:
    msg += "⚠️ لینک گپ ریل‌چت در دسترس نیست."

<<<<<<< HEAD
# ارسال پیام به کاربر
await context.bot.send_message(chat_id=user_id, text=msg)

# ویرایش کپشن پیام قبلی (فقط یک بار)
await query.message.edit_caption(caption="✅ فرم تایید و ارسال شد.")

=======
        # ارسال پیام به کاربر
        await context.bot.send_message(chat_id=user_id, text=msg)

        # ویرایش کپشن پیام قبلی (فقط یک بار)
        await query.message.edit_caption(caption="✅ فرم تایید و ارسال شد.")
        await context.bot.send_message(chat_id=user_id, text=f"📩 این لینک ورود به گروه رول شماست:\n{rol_link.rol_link}")
>>>>>>> 441097b (new update(0.5))
    elif action == "reject":
        context.chat_data[unique_id]["rejection_reason"] = ""
        context.chat_data[unique_id]["rejection_parts"] = []
        context.chat_data[unique_id]["reject_step"] = "awaiting_text"

        await query.message.edit_caption(
            caption="🟥 لطفاً دلیل رد شدن بیو رو تایپ کن:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ افزودن بخش مشکل‌دار", callback_data=f"add_reject_part_{unique_id}")],
                [InlineKeyboardButton("📤 ارسال به کاربر", callback_data=f"send_reject_{unique_id}")],
                [InlineKeyboardButton("❌ لغو", callback_data=f"cancel_reject_{unique_id}")]
            ])
        )

    elif query.data.startswith("send_reject_"):
        uid = query.data.split("_")[-1]
        data = context.chat_data.get(uid)
        if not data:
             await query.message.reply_text("❌ اطلاعات پیدا نشد.")
             return

        if not data.get("rejection_reason") or not data.get("rejection_parts"):
            await query.answer("✏️ هم متن بنویس هم حداقل یه بخش انتخاب کن!", show_alert=True)
            return

        reason = data["rejection_reason"]
        parts = "، ".join(data["rejection_parts"])
        user_id = data["user_id"]

        msg = (
            "❌ متاسفانه بیوی شما رد شد.\n\n"
            f"📌 بخش‌های مشکل‌دار: {parts}\n"
            f"📝 توضیح: {reason}"
        )

        await context.bot.send_message(chat_id=user_id, text=msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 ارسال مجدد بیو", callback_data="bio")]
        ]))

        await query.message.edit_caption("📨 دلیل رد برای کاربر ارسال شد.")
        context.chat_data.pop(uid, None)


    elif query.data.startswith("cancel_reject_"):
        uid = query.data.split("_")[-1]
        context.chat_data.pop(uid, None)
        await query.message.edit_caption("❌ عملیات رد بیو لغو شد.")



def chunk_list(lst, size):
    """تقسیم لیست به بخش‌های کوچکتر"""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

async def show_skill_selection(update, context, page=0):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
    else:
        message = update.message
        user_id = message.from_user.id

    current = user_state[user_id]
    selected = current.get("skills", [])
    total_pages = (len(skills_list) + SKILLS_PER_PAGE - 1) // SKILLS_PER_PAGE

    user_state[user_id]["skill_page"] = page
    
    # مهارت‌های این صفحه
    start = page * SKILLS_PER_PAGE
    end = start + SKILLS_PER_PAGE
    page_skills = skills_list[start:end]

    context.user_data['skills_by_page'] = context.user_data.get('skills_by_page', {})
    context.user_data['skills_by_page'][page] = page_skills

    keyboard = []
    row = []
    for i, skill in enumerate(page_skills, 1):
        selected_mark = " ✅" if skill in selected else ""
        row.append(InlineKeyboardButton(skill + selected_mark, callback_data=f"select_skill_{page}_{i-1}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # دکمه‌های ناوبری پایین صفحه
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"skill_page_{page - 1}"))
    if page + 1 < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"skill_page_{page + 1}"))
        
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    # دکمه ریست انتخاب
    if selected:
        keyboard.append([InlineKeyboardButton("🗑 حذف انتخاب‌ها", callback_data="reset_skills")])

    # اگر به ۳ تا رسیدن دکمه ادامه بده
    keyboard.append([InlineKeyboardButton("✅ ادامه", callback_data="skills_done")])

    # متن
    skill_text = "🔧 مهارت‌هات رو انتخاب کن (حداکثر ۳):\n"
    if selected:
        skill_text += "\n✅ انتخاب‌شده‌ها:\n" + "\n".join(f"🔹 {s}" for s in selected)
    else:
        skill_text += "\n⚠️ فعلاً مهارتی انتخاب نشده."

    markup = InlineKeyboardMarkup(keyboard)

    # ارسال یا ویرایش پیام
    if update.callback_query:
        await query.message.edit_text(skill_text, reply_markup=markup)
    else:
        await update.message.reply_text(skill_text, reply_markup=markup)



async def handle_skill_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    # skill = query.data.replace("select_skill_", "")
    match = re.match(r"select_skill_(\d+)_(\d+)", query.data)
    if not match:
        return  # یا لاگ کن: print(f"❌ Invalid skill select data: {query.data}")
    page_str, index_str = match.groups()
    page = int(page_str)
    index = int(index_str)
    skills_by_page = context.user_data.get("skills_by_page", {})
    page_skills = skills_by_page.get(page, [])

    if index >= len(page_skills):
        await query.answer("❌ خطا در انتخاب مهارت.")
        return

    skill = page_skills[index]
    state = user_state.get(user_id, {})
    selected = state.get("skills", [])

    if skill in selected:
        await query.answer("⚠️ این مهارت رو قبلاً انتخاب کردی!", show_alert=True)
        return

    if len(selected) >= 3:
        await query.answer("⚠️ فقط ۳ مهارت می‌تونی انتخاب کنی!", show_alert=True)
        return

    # ذخیره کن اما نرو مرحله بعد
    selected.append(skill)
    state["skills"] = selected
    if len(selected) == 3:
        state["skill1"], state["skill2"], state["skill3"] = selected
    await show_skill_selection(update, context, page=state.get("skill_page", 0))



async def handle_skill_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" not in str(e):
            raise
    user_id = query.from_user.id
    page = int(query.data.split("_")[-1])
    user_state[user_id]["skill_page"] = page
    await show_skill_selection(update, context, page)
    print(f"[Skill Nav] User {user_id} → Page {page}")


async def handle_skill_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id]["skill_page"] = 0
    user_state[user_id]["skills"] = []
    await show_skill_selection(update, context, page=0)

async def handle_skill_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    state = user_state.get(user_id, {})

    if len(state.get("skills", [])) < 3:
        await query.answer("⚠️ هنوز ۳ مهارت انتخاب نکردی.", show_alert=True)
        return

    state["step"] = "asking_appearance"
    await query.message.edit_text("💠 مشخصات ظاهری رو بنویس:")


REJECTABLE_PARTS = [
    "اسم", "لقب", "سن", "شغل", "کشور", "مهارت‌ها",
    "ظاهر", "تاریخچه", "آیدی", "هشتگ", "عکس"
]

async def handle_add_reject_part(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, _, uid = query.data.partition("add_reject_part_")
    data = context.chat_data.get(uid)
    if not data:
        await query.message.reply_text("❌ فرم یافت نشد.")
        return

    keyboard = [[InlineKeyboardButton(p, callback_data=f"part_{uid}_{p}")] for p in REJECTABLE_PARTS]
    await query.message.reply_text("📌 بخش‌هایی که مشکل دارن رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_reject_part_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, uid, part = query.data.split("_", 2)
    data = context.chat_data.get(uid)
    if not data:
        return

    if part not in data["rejection_parts"]:
        data["rejection_parts"].append(part)
        await query.answer(f"✅ بخش «{part}» اضافه شد.")
    else:
        await query.answer("⚠️ این بخش قبلاً اضافه شده.", show_alert=True)

# راه‌اندازی ربات
app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_skill_navigation, pattern="^skill_page_"))  # اول بیاد
app.add_handler(CallbackQueryHandler(handle_skill_reset, pattern="^reset_skills$"))
app.add_handler(CallbackQueryHandler(handle_skill_continue, pattern="^skills_done$"))
app.add_handler(CallbackQueryHandler(handle_skill_selection, pattern="^select_skill_"))  # بعد از بقیه بیاد
app.add_handler(CallbackQueryHandler(select_job, pattern="^select_country_"))
app.add_handler(CallbackQueryHandler(ask_bio_fields, pattern="^job_"))
app.add_handler(CallbackQueryHandler(handle_job_actions, pattern="^(add|remove|increase|decrease)_job_"))
app.add_handler(CallbackQueryHandler(show_country_jobs, pattern="^manage_jobs_"))
app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(approve|reject)_bio_"))
app.add_handler(CallbackQueryHandler(handle_add_reject_part, pattern="^add_reject_part_"))
app.add_handler(CallbackQueryHandler(handle_reject_part_selection, pattern="^part_"))
app.add_handler(CallbackQueryHandler(handle_bio_approval, pattern="^(send_reject|cancel_reject)_"))
app.add_handler(CallbackQueryHandler(handle_main_menu))
# app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_all_messages))
app.add_handler(MessageHandler(pv_filter & filters.PHOTO, collect_bio))
app.add_handler(MessageHandler(pv_filter & filters.TEXT & (~filters.COMMAND), handle_all_messages))


if __name__ == "__main__":
    print(f"✅ Bot is running on port {PORT} via webhook")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://rotc-telegram-bot.onrender.com/{BOT_TOKEN}",
        # secret_token=BOT_TOKEN,
    )
