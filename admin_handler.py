
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import jobs_by_country, skills_config, save_data, load_bios, remove_bio_from_storage, remove_used_hashtag, remove_used_hashtag
from keyboards import bio_admin_menu, country_selection_keyboard, job_management_keyboard, skill_management_keyboard, bio_approval_keyboard, admin_back_buttons, skill_type_selection_keyboard
from utils import format_bio_text
from config import BIO_CHANNEL, ROLE_CHAT_ID, REALCHAT_ID

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("با حضورتون منورمون کردین😔✨",
                                  reply_markup=bio_admin_menu())

async def show_admin_job_list(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🌍 مشاغل کدوم کشور و میخوای انگشت کنی؟",
        reply_markup=country_selection_keyboard("manage_jobs"))

async def show_admin_skill_list(update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    normal_skills = skills_config.get("normal", [])
    special_skills = skills_config.get("special", [])

    skills_text = "📘 مهارت‌های عادی:\n" + "\n".join(f"🔹 {s}" for s in normal_skills)
    skills_text += "\n\n💠 مهارت‌های خاص:\n" + "\n".join(f"🔸 {s}" for s in special_skills)
    await query.message.edit_text(skills_text,
                                  reply_markup=skill_management_keyboard()
                                 )

async def show_country_jobs(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    country = data.split("_")[2]

    jobs = jobs_by_country.get(country)
    if not jobs:
        await query.message.edit_text("❌ کشور پیدا نشد.",
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton(
                                              "🔙 برگشت",
                                              callback_data="back_to_main")
                                      ]]))
        return

    text = f"👥 لیست مشاغل توی کشور {country}:\n"
    for job in jobs:
        text += f"🔹 {job['name']} - لول: {job['level']} - ظرفیت باقی‌مانده: {job['count']}\n"

    job_buttons = [
        [
            InlineKeyboardButton("➕ اضافه کردن شغل",
                                 callback_data=f"add_job_{country}")
        ],
        [
            InlineKeyboardButton("❌ حذف شغل",
                                 callback_data=f"remove_job_{country}")
        ],
        [
            InlineKeyboardButton("🔼 افزایش ظرفیت",
                                 callback_data=f"increase_job_{country}")
        ],
        [
            InlineKeyboardButton("🔽 کاهش ظرفیت",
                                 callback_data=f"decrease_job_{country}")
        ],
        [InlineKeyboardButton("🔙 برگشتن", callback_data="back_to_admin_menu")]
    ]

    await query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(job_buttons))

async def handle_job_actions(update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    action, country = data.split("_job_")

    # Store state in context.user_data instead of global user_state
    context.user_data[user_id] = {"step": f"{action}_job", "country": country, "previous_step": "country_jobs"}

    if action == "add":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="📝 فرمت افزودن شغل:\nنام شغل - لول - ظرفیت\nمثال: شکارچی - 2 - 3",
            reply_markup=admin_back_buttons())
    elif action == "remove":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ نام شغلی که می‌خوای حذف کنی رو بنویس:",
            reply_markup=admin_back_buttons())
    elif action == "increase":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🔼 بنویس: نام شغل - تعداد افزایش\nمثال: دکتر - 2",
            reply_markup=admin_back_buttons())
    elif action == "decrease":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🔽 بنویس: نام شغل - تعداد کاهش\nمثال: دکتر - 1",
            reply_markup=admin_back_buttons())

async def handle_skill_actions(update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add_skill":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🧪 نوع مهارتی که می‌خوای اضافه کنی رو انتخاب کن:",
            reply_markup=skill_type_selection_keyboard()
        )
        context.user_data[user_id] = {
            "step": "choosing_skill_type",
            "previous_step": "admin_skill_list"
        }
    elif query.data == "remove_skill":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🗑 اسم مهارتی که می‌خوای حذف کنی رو بنویس:",
            reply_markup=admin_back_buttons())
        context.user_data[user_id] = {"step": "removing_skill", "previous_step": "admin_skill_list"}

async def handle_admin_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = context.user_data.get(user_id, {})

    step = state.get("step")

    # افزودن مهارت
    if step == "awaiting_skill_name":
        skill_type = state.get("skill_type")
        skill_list = skills_config.get(skill_type, [])

        if text in skill_list:
            await update.message.reply_text("⚠️ این مهارت قبلاً ثبت شده. لطفاً اسم دیگه‌ای بزن.")
            return

        skills_config[skill_type].append(text)

        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_config": skills_config
        })

        await update.message.reply_text(
            f"✅ مهارت جدید به لیست {'عادی' if skill_type == 'normal' else 'خاص'} اضافه شد.",
            reply_markup=skill_management_keyboard()
        )
        context.user_data.pop(user_id, None)

    # حذف مهارت
    elif step == "removing_skill":
        # بررسی در هر دو لیست
        for skill_type in ["normal", "special"]:
            if text in skills_config.get(skill_type, []):
                skills_config[skill_type].remove(text)

                save_data({
                    "jobs_by_country": jobs_by_country,
                    "skills_config": skills_config
                })

                await update.message.reply_text(
                    f"🗑 مهارت «{text}» از لیست {'عادی' if skill_type == 'normal' else 'خاص'} حذف شد.",
                    reply_markup=skill_management_keyboard()
                )
                context.user_data.pop(user_id, None)
                return

        # اگر در هیچ لیستی نبود
        await update.message.reply_text("❌ مهارت مورد نظر در لیست پیدا نشد. لطفاً مجدد بررسی کن.")

async def handle_bio_approval(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, _, unique_id = query.data.partition("_bio_")

    bios = load_bios()
    bio_data = bios.get("bios", {}).get(unique_id)

    if not bio_data:
        await query.message.edit_caption(
            caption=
            "❌ یا اطلاعات بیشتر از 7 روز ول بوده حذف شده یا قبلا بررسی کردی بازم حذف شده لپ کلام پیداش نکردم تو دیتابیس"
        )
        return

    user_id = int(unique_id)
    photo = bio_data["photo"]
    caption = format_bio_text(bio_data)

    if action == "approve":
        await query.message.edit_reply_markup(reply_markup=None)
        country = bio_data["country"]
        job_name = bio_data["job"]
        
        # For approval, we don't change job count since it's permanently taken
        # The job was already reserved and removed from available count
        
        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_config": skills_config
        })

        # Send to bio channel
        await context.bot.send_photo(chat_id=BIO_CHANNEL,
                                     photo=photo,
                                     caption=caption)

        # Send approval message to user
        await context.bot.send_message(
            chat_id=user_id, text="✅ فرم بیوت تایید شد گذاشتمش تو چنل بیو.")

        # Create invite links
        rol_link = None
        realchat_link = None

        try:
            invite_rol = await context.bot.create_chat_invite_link(
                chat_id=ROLE_CHAT_ID,
                member_limit=1,
                creates_join_request=False)
            rol_link = invite_rol.invite_link
        except Exception as e:
            print(f"❌خطا یحتمل ادمینم نکردی تو گپ رول: {e}")

        try:
            invite_realchat = await context.bot.create_chat_invite_link(
                chat_id=REALCHAT_ID,
                member_limit=1,
                creates_join_request=False)
            realchat_link = invite_realchat.invite_link
        except Exception as e:
            print(f"❌ خطا یحتمل ادمینم نکردی تو گپ ریل: {e}")

        # Send final message to user
        msg = "📩 لینک اختصاصی ساختم برات برو عشق کن:\n"
        if rol_link:
            msg += f"🔷 گپ رول: {rol_link}\n"
        else:
            msg += "⚠️ لینک گپ رول در دسترس نیست.\n"

        if realchat_link:
            msg += f"🔸 گپ ریل‌چت: {realchat_link}"
        else:
            msg += "⚠️ لینک گپ ریل‌چت در دسترس نیست."

        await context.bot.send_message(chat_id=user_id, text=msg)
        remove_bio_from_storage(user_id)

        await context.bot.send_message(chat_id=query.from_user.id,
                                       text="✅ فرم تایید و ارسال شد.")

    elif action == "reject":
        await query.message.edit_reply_markup(reply_markup=None)
        user_id = int(unique_id)
        admin_username = query.from_user.username or "admin"

        # Return job capacity since bio was rejected
        country = bio_data.get("country")
        job_name = bio_data.get("job")

        if country and job_name:
            job_data = next((j for j in jobs_by_country.get(country, [])
                             if j["name"] == job_name), None)
            if job_data:
                job_data["count"] += 1
                save_data({
                    "jobs_by_country": jobs_by_country,
                    "skills_config": skills_config
                })

        # Send rejection message to user
        await context.bot.send_message(
            chat_id=user_id,
            text=
            f"❌ بیوتو ادمین بی‌رحم رد کرده.\nبرو بگو چرا رد کردی، خودم پشتتم (الکی) @{admin_username}",
        )

        tag = bio_data.get("user_id_tag")
        if tag:
            remove_used_hashtag(tag)

        # Remove bio from storage (this also removes the hashtag from used list)
        remove_bio_from_storage(user_id)

        # Send confirmation to admin
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=
            "🤧 خبر رد شدنش بهش رسید 📨 راحت شدی؟ نه الان خوشحالی ردش کردی؟ بی‌رحم!",
            reply_to_message_id=query.message.message_id)
