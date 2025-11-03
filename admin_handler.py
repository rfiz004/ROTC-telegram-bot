from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from data_manager import jobs_by_country, skills_config, save_data_file, save_data_file, load_bios, remove_bio_from_storage, remove_used_hashtag, country_group_ids, save_bios, load_data_file, save_data, load_job_reservations, save_job_reservations
from keyboards import bio_admin_menu, country_selection_keyboard, job_management_keyboard, skill_management_keyboard, bio_approval_keyboard, admin_back_buttons, skill_type_selection_keyboard
from utils import format_bio_text
from config import BIO_CHANNEL, ROLE_CHAT_ID, REALCHAT_ID, BIO_ADMIN_ID
import logging

logger = logging.getLogger(__name__)

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu based on user role"""
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ دسترسی غیرمجاز.")
        else:
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
        return

    menu_text = "با حضورتون منورمون کردین😔✨"

    if update.callback_query:
        await update.callback_query.edit_message_text(menu_text, reply_markup=bio_admin_menu())
    else:
        await update.message.reply_text(menu_text, reply_markup=bio_admin_menu())

async def show_admin_job_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin job management interface"""
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ دسترسی غیرمجاز.")
        else:
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
        return

    text = "🌍 مشاغل کدوم کشور و میخوای انگشت کنی؟"
    keyboard = country_selection_keyboard("manage_jobs")

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def show_admin_skill_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin skill management interface"""
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ دسترسی غیرمجاز.")
        else:
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
        return

    try:
        normal_skills = skills_config.get("normal", [])
        special_skills = skills_config.get("special", [])

        skills_text = "📘 مهارت‌های عادی:\n" + "\n".join(f"🔹 {s}" for s in normal_skills)
        skills_text += "\n\n💠 مهارت‌های خاص:\n" + "\n".join(f"🔸 {s}" for s in special_skills)

        if update.callback_query:
            await update.callback_query.edit_message_text(skills_text, reply_markup=skill_management_keyboard())
        else:
            await update.message.reply_text(skills_text, reply_markup=skill_management_keyboard())
    except Exception as e:
        logger.error(f"Error in show_admin_skill_list: {e}")
        error_text = "❌ خطا در نمایش مهارت‌ها"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text, reply_markup=admin_back_buttons())
        else:
            await update.message.reply_text(error_text, reply_markup=admin_back_buttons())

async def show_country_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show jobs for a specific country"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        await query.edit_message_text("❌ دسترسی غیرمجاز.")
        return

    try:
        country = query.data.replace("manage_jobs_", "")
        from data_manager import jobs_by_country
        jobs = jobs_by_country.get(country, [])

        text = f"👥 لیست مشاغل توی کشور {country}:\n\n"
        if jobs:
            for job in jobs:
                job_name = job.get('name', 'نامشخص')
                job_level = job.get('level', 1)
                job_count = job.get('count', 0)
                text += f"🔹 {job_name} - لول: {job_level} - ظرفیت باقی‌مانده: {job_count}\n"
        else:
            text += "هیچ شغلی تعریف نشده است."

        from keyboards import job_management_keyboard, admin_back_buttons
        await query.edit_message_text(text, reply_markup=job_management_keyboard(country))
    except Exception as e:
        logger.error(f"Error in show_country_jobs: {e}")
        from keyboards import admin_back_buttons
        await query.edit_message_text("❌ خطا در نمایش مشاغل کشور", reply_markup=admin_back_buttons())

async def handle_job_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle job management actions"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_data = context.user_data.get(user_id, {})
    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        await query.edit_message_text("❌ دسترسی غیرمجاز.")
        return

    try:
        data_parts = query.data.split("_")
        if len(data_parts) < 3:
            await query.edit_message_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())
            return

        action = data_parts[0]
        country = "_".join(data_parts[2:])  # Handle country names with underscores

        context.user_data[user_id] = {
            "step": f"{action}_job", 
            "country": country, 
            "action_type": f"{action}_job",
            "previous_step": "country_jobs"
        }

        if action == "add":
            await query.edit_message_text(
                f"📝 فرمت افزودن شغل:\nنام شغل - لول - ظرفیت\nمثال: شکارچی - 2 - 3",
                reply_markup=admin_back_buttons()
            )
        elif action == "remove":
            await query.edit_message_text(
                f"❌ نام شغلی که می‌خوای حذف کنی رو بنویس:",
                reply_markup=admin_back_buttons()
            )
        elif action == "increase":
            await query.edit_message_text(
                f"🔼 بنویس: نام شغل - تعداد افزایش\nمثال: دکتر - 2",
                reply_markup=admin_back_buttons()
            )
        elif action == "decrease":
            await query.edit_message_text(
                f"🔽 بنویس: نام شغل - تعداد کاهش\nمثال: دکتر - 1",
                reply_markup=admin_back_buttons()
            )
        else:
            await query.edit_message_text("❌ عملیات نامعتبر.", reply_markup=admin_back_buttons())
    except Exception as e:
        logger.error(f"Error in handle_job_actions: {e}")
        await query.edit_message_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())

async def handle_skill_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle skill management actions"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        await query.edit_message_text("❌ دسترسی غیرمجاز.")
        return

    try:
        action = query.data

        if action == "add_skill":
            context.user_data[user_id] = {
                "step": "choosing_skill_type",
                "previous_step": "admin_skill_list"
            }
            await query.edit_message_text(
                "🧪 نوع مهارتی که می‌خوای اضافه کنی رو انتخاب کن:",
                reply_markup=skill_type_selection_keyboard()
            )
        elif action == "remove_skill":
            context.user_data[user_id] = {
                "step": "removing_skill", 
                "previous_step": "admin_skill_list"
            }
            await query.edit_message_text(
                "🗑 اسم مهارتی که می‌خوای حذف کنی رو بنویس:",
                reply_markup=admin_back_buttons()
            )
    except Exception as e:
        logger.error(f"Error in handle_skill_actions: {e}")
        await query.edit_message_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())

async def handle_bio_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bio approval/rejection"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if update.effective_user.id not in BIO_ADMIN_ID:
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ دسترسی غیرمجاز.")
        return

    try:
        action_parts = query.data.split("_")
        if len(action_parts) < 3:
            await context.bot.send_message(chat_id=query.message.chat.id, text="❌ خطا در پردازش درخواست.")
            return

        action = action_parts[0]
        bio_user_id = int(action_parts[2])

        bios = load_bios()
        bios_dict = bios.get("bios", {})
        user_bio = bios_dict.get(str(bio_user_id))


        if not user_bio:
            await context.bot.send_message(chat_id=query.message.chat.id, text="❌ بیوگرافی پیدا نشد.")
            return


        # if action == "approve":
        #     await query.message.edit_reply_markup(reply_markup=None)

        #     user_id = int(user_bio.get("unique_id"))
        #     photo = user_bio.get("photo")
        #     caption = format_bio_text(user_bio)

        #     country = user_bio.get("country")
        #     job_name = user_bio.get("job")

        #     # برای تایید، نیاز نیست ظرفیت شغل کم بشه (قبلا رزرو شده)
        #     save_data_file({
        #         "jobs_by_country": jobs_by_country,
        #         "skills_config": skills_config
        #     })

        #     # ارسال عکس + کپشن به کانال بیو
        #     await context.bot.send_photo(chat_id=BIO_CHANNEL, photo=photo, caption=caption)

        #     # پیام تایید به کاربر
        #     await context.bot.send_message(chat_id=user_id, text="✅ فرم بیوت تایید شد گذاشتمش تو چنل بیو.")

        #     # ساخت لینک‌های دعوت
        #     rol_link, realchat_link, country_link = None, None, None

        #     try:
        #         invite_rol = await context.bot.create_chat_invite_link(
        #             chat_id=ROLE_CHAT_ID, member_limit=1, creates_join_request=False)
        #         rol_link = invite_rol.invite_link
        #     except Exception as e:
        #         logger.error(f"❌خطا در ساخت لینک گپ رول: {e}")

        #     try:
        #         invite_realchat = await context.bot.create_chat_invite_link(
        #             chat_id=REALCHAT_ID, member_limit=1, creates_join_request=False)
        #         realchat_link = invite_realchat.invite_link
        #     except Exception as e:
        #         logger.error(f"❌ خطا در ساخت لینک گپ ریل‌چت: {e}")

        #     try:
        #         group_id = country_group_ids.get(country)
        #         if group_id:
        #             invite_country = await context.bot.create_chat_invite_link(
        #                 chat_id=group_id, member_limit=1, creates_join_request=False)
        #             country_link = invite_country.invite_link
        #     except Exception as e:
        #         logger.error(f"❌ خطا در ساخت لینک گروه کشور {country}: {e}")

        #     # ارسال پیام نهایی به کاربر با لینک‌ها
        #     msg = "📩 لینک اختصاصی ساختم برات برو عشق کن:\n"
        #     msg += f"🔷 گپ رول: {rol_link}\n" if rol_link else "⚠️ لینک گپ رول در دسترس نیست.\n"
        #     msg += f"🔸 گپ ریل‌چت: {realchat_link}\n" if realchat_link else "⚠️ لینک گپ ریل‌چت در دسترس نیست.\n"
        #     msg += f"🌍 گروه کشور {country}: {country_link}" if country_link else f"⚠️ لینک گروه کشور {country} پیدا نشد یا قابل ساخت نبود."

        #     await context.bot.send_message(chat_id=user_id, text=msg)

        #     # حذف بیو از ذخیره‌سازی
        #     remove_bio_from_storage(user_id)

        #     # اطلاع ادمین از تایید
        #     await context.bot.send_message(chat_id=query.from_user.id, text="✅ فرم تایید و ارسال شد.")

        # if action == "approve":
        #     await query.message.edit_reply_markup(reply_markup=None)
        
        #     user_id = int(user_bio.get("unique_id"))
        #     photo = user_bio.get("photo")
        #     caption = format_bio_text(user_bio)
        
        #     country = user_bio.get("country")
        #     job_name = user_bio.get("job")
        
        #     # حذف رزرو از فایل job_reservations
        #     reservations = load_job_reservations()
        #     if str(user_id) in reservations:
        #         del reservations[str(user_id)]
        #         save_job_reservations(reservations)
        #         logger.info(f"🗑 رزرو شغل برای کاربر {user_id} حذف شد (تایید توسط ادمین).")
        
        #     # برای تایید، نیاز نیست ظرفیت شغل کم بشه (قبلا رزرو شده)
        #     save_data_file({
        #         "jobs_by_country": jobs_by_country,
        #         "skills_config": skills_config
        #     })
        
        #     # ارسال عکس + کپشن به کانال بیو
        #     await context.bot.send_photo(chat_id=BIO_CHANNEL, photo=photo, caption=caption)
        
        #     # پیام تایید به کاربر
        #     await context.bot.send_message(chat_id=user_id, text="✅ فرم بیوت تایید شد گذاشتمش تو چنل بیو.")
        
        #     # ساخت لینک‌های دعوت
        #     rol_link, realchat_link, country_link = None, None, None
        
        #     try:
        #         invite_rol = await context.bot.create_chat_invite_link(
        #             chat_id=ROLE_CHAT_ID, member_limit=1, creates_join_request=False)
        #         rol_link = invite_rol.invite_link
        #     except Exception as e:
        #         logger.error(f"❌ خطا در ساخت لینک گپ رول: {e}")
        
        #     try:
        #         invite_realchat = await context.bot.create_chat_invite_link(
        #             chat_id=REALCHAT_ID, member_limit=1, creates_join_request=False)
        #         realchat_link = invite_realchat.invite_link
        #     except Exception as e:
        #         logger.error(f"❌ خطا در ساخت لینک گپ ریل‌چت: {e}")
        
        #     try:
        #         group_id = country_group_ids.get(country)
        #         if group_id:
        #             invite_country = await context.bot.create_chat_invite_link(
        #                 chat_id=group_id, member_limit=1, creates_join_request=False)
        #             country_link = invite_country.invite_link
        #     except Exception as e:
        #         logger.error(f"❌ خطا در ساخت لینک گروه کشور {country}: {e}")
        
        #     # ارسال پیام نهایی به کاربر با لینک‌ها
        #     msg = "📩 لینک اختصاصی ساختم برات برو عشق کن:\n"
        #     msg += f"🔷 گپ رول: {rol_link}\n" if rol_link else "⚠️ لینک گپ رول در دسترس نیست.\n"
        #     msg += f"🔸 گپ ریل‌چت: {realchat_link}\n" if realchat_link else "⚠️ لینک گپ ریل‌چت در دسترس نیست.\n"
        #     msg += f"🌍 گروه کشور {country}: {country_link}" if country_link else f"⚠️ لینک گروه کشور {country} پیدا نشد یا قابل ساخت نبود."
        
        #     await context.bot.send_message(chat_id=user_id, text=msg)
        
        #     # حذف بیو از ذخیره‌سازی
        #     remove_bio_from_storage(user_id)
        
        #     # اطلاع ادمین از تایید
        #     await context.bot.send_message(chat_id=query.from_user.id, text="✅ فرم تایید و ارسال شد.")

        if action == "approve":
            await query.message.edit_reply_markup(reply_markup=None)

            user_id = int(user_bio.get("unique_id"))
            photos = user_bio.get("photos", [])
            caption = format_bio_text(user_bio)

            country = user_bio.get("country")
            job_name = user_bio.get("job")

            # حذف رزرو از فایل job_reservations
            reservations = load_job_reservations()
            if str(user_id) in reservations:
                del reservations[str(user_id)]
                save_job_reservations(reservations)
                logger.info(f"🗑 رزرو شغل برای کاربر {user_id} حذف شد (تایید توسط ادمین).")

            save_data_file({
                "jobs_by_country": jobs_by_country,
                "skills_config": skills_config
            })

            # ارسال کل آلبوم به کانال با کپشن زیر اولین عکس
            if photos:
                media_group = []
                for i, pid in enumerate(photos):
                    if i == 0:
                        media_group.append(InputMediaPhoto(media=pid, caption=caption, parse_mode="HTML"))
                    else:
                        media_group.append(InputMediaPhoto(media=pid))
                await context.bot.send_media_group(chat_id=BIO_CHANNEL, media=media_group)

            # پیام تایید به کاربر
            await context.bot.send_message(chat_id=user_id, text="✅ فرم بیوت تایید شد و در چنل بیو گذاشته شد.")

            # ساخت لینک‌های دعوت
            rol_link, realchat_link, country_link = None, None, None

            try:
                invite_rol = await context.bot.create_chat_invite_link(
                    chat_id=ROLE_CHAT_ID, member_limit=1, creates_join_request=False)
                rol_link = invite_rol.invite_link
            except Exception as e:
                logger.error(f"❌ خطا در ساخت لینک گپ رول: {e}")

            try:
                invite_realchat = await context.bot.create_chat_invite_link(
                    chat_id=REALCHAT_ID, member_limit=1, creates_join_request=False)
                realchat_link = invite_realchat.invite_link
            except Exception as e:
                logger.error(f"❌ خطا در ساخت لینک گپ ریل‌چت: {e}")

            try:
                group_id = country_group_ids.get(country)
                if group_id:
                    invite_country = await context.bot.create_chat_invite_link(
                        chat_id=group_id, member_limit=1, creates_join_request=False)
                    country_link = invite_country.invite_link
            except Exception as e:
                logger.error(f"❌ خطا در ساخت لینک گروه کشور {country}: {e}")

            # ارسال لینک‌ها به کاربر
            msg = "📩 لینک اختصاصی ساختم برات برو عشق کن:\n"
            msg += f"🔷 گپ رول: {rol_link}\n" if rol_link else "⚠️ لینک گپ رول در دسترس نیست.\n"
            msg += f"🔸 گپ ریل‌چت: {realchat_link}\n" if realchat_link else "⚠️ لینک گپ ریل‌چت در دسترس نیست.\n"
            msg += f"🌍 گروه کشور {country}: {country_link}" if country_link else f"⚠️ لینک گروه کشور {country} پیدا نشد یا قابل ساخت نبود."
            await context.bot.send_message(chat_id=user_id, text=msg)

            # حذف بیو از ذخیره‌سازی
            remove_bio_from_storage(user_id)

            # اطلاع ادمین از تایید
            await context.bot.send_message(chat_id=query.from_user.id, text="✅ فرم تایید و ارسال شد.")




        
        # elif action == "reject":
        #     await query.message.edit_reply_markup(reply_markup=None)
    
        #     user_id = int(user_bio.get("unique_id"))
        #     admin_username = query.from_user.username or "admin"
    
        #     # بازگرداندن ظرفیت شغل به دلیل رد شدن بیو
        #     country = user_bio.get("country")
        #     job_name = user_bio.get("job")
    
        #     if country and job_name:
        #         job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job_name), None)
        #         if job_data:
        #             job_data["count"] += 1
        #             save_data_file({
        #                 "jobs_by_country": jobs_by_country,
        #                 "skills_config": skills_config
        #             })
    
        #     # ارسال پیام رد به کاربر
        #     await context.bot.send_message(
        #         chat_id=user_id,
        #         text=(
        #             f"❌ بیوتو ادمین بی‌رحم رد کرده.\n"
        #             f"برو بگو چرا رد کردی، خودم پشتتم (الکی) @{admin_username}"
        #         ),
        #     )
    
        #     tag = user_bio.get("user_id_tag")
        #     if tag:
        #         remove_used_hashtag(tag)
    
        #     # حذف بیو از ذخیره‌سازی
        #     remove_bio_from_storage(user_id)
    
        #     # ارسال پیام تایید به ادمین
        #     await context.bot.send_message(
        #         chat_id=query.message.chat.id,
        #         text="🤧 خبر رد شدنش بهش رسید 📨 راحت شدی؟ نه الان خوشحالی ردش کردی؟ بی‌رحم!",
        #         reply_to_message_id=query.message.message_id
        #     )


        elif action == "reject":
            await query.message.edit_reply_markup(reply_markup=None)
        
            user_id = int(user_bio.get("unique_id"))
            admin_username = query.from_user.username or "admin"
        
            country = user_bio.get("country")
            job_name = user_bio.get("job")
        
            # 🗑 حذف رزرو از فایل job_reservations
            reservations = load_job_reservations()
            if str(user_id) in reservations:
                del reservations[str(user_id)]
                save_job_reservations(reservations)
                logger.info(f"🗑 رزرو شغل برای کاربر {user_id} ({job_name}) حذف شد (رد توسط ادمین).")
        
            # بازگرداندن ظرفیت شغل
            if country and job_name:
                job_data = next((j for j in jobs_by_country.get(country, []) if j["name"] == job_name), None)
                if job_data:
                    job_data["count"] += 1
                    save_data_file({
                        "jobs_by_country": jobs_by_country,
                        "skills_config": skills_config
                    })
        
            # ارسال پیام رد به کاربر
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ بیوتو ادمین بی‌رحم رد کرده.\n"
                    f"برو بگو چرا رد کردی، خودم پشتتم (الکی) @{admin_username}"
                ),
            )
        
            tag = user_bio.get("user_id_tag")
            if tag:
                remove_used_hashtag(tag)
        
            # حذف بیو از ذخیره‌سازی
            remove_bio_from_storage(user_id)
        
            # ارسال پیام تایید به ادمین
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="🤧 خبر رد شدنش بهش رسید 📨 راحت شدی؟ نه الان خوشحالی ردش کردی؟ بی‌رحم!",
                reply_to_message_id=query.message.message_id
            )

    
    except Exception as e:
        logger.error(f"Error in handle_bio_approval: {e}")
        await context.bot.send_message(chat_id=query.message.chat.id, text="❌ خطا در پردازش درخواست.")

async def show_pending_bios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending bios for approval"""
    user_id = update.effective_user.id
    user_data = context.user_data.get(user_id, {})

    from utils import check_admin_access
    if not check_admin_access(user_data, required_role="bio_admin"):
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ دسترسی غیرمجاز.")
        else:
            await update.message.reply_text("❌ دسترسی غیرمجاز.")
        return

    try:
        bios = load_bios()
        # Filter pending bios and handle mixed formats
        pending_bios = []
        for bio in bios:
            if isinstance(bio, dict) and not bio.get("approved", False):
                pending_bios.append(bio)
            elif isinstance(bio, str):
                # Skip malformed string entries
                continue

        if not pending_bios:
            text = "✅ هیچ بیوگرافی در انتظار تأیید نیست."
            keyboard = admin_back_buttons()
        else:
            bio = pending_bios[0]  # Show first pending bio
            text = f"📋 بیوگرافی در انتظار تأیید:\n\n{format_bio_text(bio)}"
            keyboard = bio_approval_keyboard(str(bio.get('user_id', '')))

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error in show_pending_bios: {e}")
        error_text = "❌ خطا در نمایش بیوگرافی‌های در انتظار"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text, reply_markup=admin_back_buttons())
        else:
            await update.message.reply_text(error_text, reply_markup=admin_back_buttons())



# async def handle_admin_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle admin text message inputs"""
#     user_id = update.message.from_user.id
#     text = update.message.text.strip()
#     user_data = context.user_data.get(user_id, {})
#     step = user_data.get("step")

#     try:
#         # Handle skill management
#         if step == "awaiting_skill_name":
#             skill_type = user_data.get("skill_type")
#             if not skill_type:
#                 await update.message.reply_text("❌ نوع مهارت مشخص نیست.")
#                 return

#             skill_list = skills_config.get(skill_type, [])

#             if text in skill_list:
#                 await update.message.reply_text("⚠️ این مهارت قبلاً ثبت شده. لطفاً اسم دیگه‌ای بزن.")
#                 return

#             skills_config[skill_type].append(text)
#             save_data_file({
#                 "jobs_by_country": jobs_by_country,
#                 "skills_config": skills_config
#             })

#             await update.message.reply_text(
#                 f"✅ مهارت جدید به لیست {'عادی' if skill_type == 'normal' else 'خاص'} اضافه شد.",
#                 reply_markup=skill_management_keyboard()
#             )
#             context.user_data.pop(user_id, None)

#         elif step == "removing_skill":
#             # Check in both lists
#             skill_found = False
#             for skill_type in ["normal", "special"]:
#                 if text in skills_config.get(skill_type, []):
#                     skills_config[skill_type].remove(text)
#                     skill_found = True
#                     break

#             if skill_found:
#                 save_data_file({
#                     "jobs_by_country": jobs_by_country,
#                     "skills_config": skills_config
#                 })
#                 await update.message.reply_text(
#                     f"✅ مهارت '{text}' از لیست حذف شد.",
#                     reply_markup=skill_management_keyboard()
#                 )
#             else:
#                 await update.message.reply_text("❌ مهارت مورد نظر در لیست پیدا نشد.")

#             context.user_data.pop(user_id, None)

#         # Handle job management
#         elif step in ["add_job", "remove_job", "increase_job", "decrease_job"]:
#             country = user_data.get("country")
#             if not country:
#                 await update.message.reply_text("❌ کشور مشخص نیست.")
#                 return

#             jobs = jobs_by_country.get(country, [])

#             if step == "add_job":
#                 # Parse format: "job_name - level - capacity"
#                 try:
#                     # Replace non-standard dashes with standard dash
#                     text = text.replace("–", "-").replace("—", "-").replace("−", "-").replace("ـ", "-")
#                     parts = [part.strip() for part in text.split("-")]
#                     if len(parts) != 3:
#                         await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - لول - ظرفیت")
#                         return

#                     job_name, level_str, capacity_str = parts
#                     level = int(level_str)
#                     capacity = int(capacity_str)

#                     # Check if job already exists
#                     if any(job.get("name") == job_name for job in jobs):
#                         await update.message.reply_text(f"❌ شغل '{job_name}' قبلاً وجود دارد.")
#                         return

#                     # Add new job
#                     new_job = {
#                         "name": job_name,
#                         "level": level,
#                         "count": capacity
#                     }
#                     jobs.append(new_job)

#                     save_data_file({
#                         "jobs_by_country": jobs_by_country,
#                         "skills_config": skills_config
#                     })

#                     await update.message.reply_text(f"✅ شغل '{job_name}' با موفقیت اضافه شد.", reply_markup=admin_back_buttons())

#                 except ValueError:
#                     await update.message.reply_text("❌ لول و ظرفیت باید عدد باشند.")

#             elif step == "remove_job":
#                 job_to_remove = None
#                 for job in jobs:
#                     if job.get("name") == text:
#                         job_to_remove = job
#                         break

#                 if job_to_remove:
#                     jobs.remove(job_to_remove)
#                     save_data_file({
#                         "jobs_by_country": jobs_by_country,
#                         "skills_config": skills_config
#                     })
#                     await update.message.reply_text(f"✅ شغل '{text}' حذف شد.", reply_markup=admin_back_buttons())
#                 else:
#                     await update.message.reply_text(f"❌ شغل '{text}' پیدا نشد.")

#             elif step in ["increase_job", "decrease_job"]:
#                 # Parse format: "job_name - amount"
#                 try:
#                     # Replace non-standard dashes with standard dash
#                     text = text.replace("–", "-").replace("—", "-").replace("−", "-").replace("ـ", "-")
#                     parts = [part.strip() for part in text.split("-")]
#                     if len(parts) != 2:
#                         await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - تعداد")
#                         return

#                     job_name, amount_str = parts
#                     amount = int(amount_str)

#                     job_found = False
#                     for job in jobs:
#                         if job.get("name") == job_name:
#                             if step == "increase_job":
#                                 job["count"] = job.get("count", 0) + amount
#                             else:  # decrease_job
#                                 job["count"] = max(0, job.get("count", 0) - amount)
#                             job_found = True
#                             break

#                     if job_found:
#                         save_data_file({
#                             "jobs_by_country": jobs_by_country,
#                             "skills_config": skills_config
#                         })
#                         action_text = "افزایش" if step == "increase_job" else "کاهش"
#                         await update.message.reply_text(f"✅ ظرفیت شغل '{job_name}' {action_text} یافت.", reply_markup=admin_back_buttons())
#                     else:
#                         await update.message.reply_text(fhandle_admin_text_message"❌ شغل '{job_name}' پیدا نشد.")

#                 except ValueError:
#                     await update.message.reply_text("❌ تعداد باید عدد باشد.")

#             context.user_data.pop(user_id, None)

#     except Exception as e:
#         logger.error(f"Error in handle_admin_text_message: {e}")
#         await update.message.reply_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())


async def handle_admin_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text message inputs"""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")

    # Normalize dashes to standard "-"
    text = text.replace("–", "-").replace("—", "-").replace("−", "-").replace("ـ", "-")

    try:
        # ========== SKILL MANAGEMENT ==========
        if step == "awaiting_skill_name":
            skill_type = user_data.get("skill_type")
            if not skill_type:
                await update.message.reply_text("❌ نوع مهارت مشخص نیست.")
                return

            skill_list = skills_config.get(skill_type, [])
            if text in skill_list:
                await update.message.reply_text("⚠️ این مهارت قبلاً ثبت شده. لطفاً اسم دیگه‌ای بزن.")
                return

            skills_config[skill_type].append(text)
            save_data_file({
                "jobs_by_country": jobs_by_country,
                "skills_config": skills_config
            })

            await update.message.reply_text(
                f"✅ مهارت جدید به لیست {'عادی' if skill_type == 'normal' else 'خاص'} اضافه شد.",
                reply_markup=skill_management_keyboard()
            )

        elif step == "removing_skill":
            skill_found = False
            for skill_type in ["normal", "special"]:
                if text in skills_config.get(skill_type, []):
                    skills_config[skill_type].remove(text)
                    skill_found = True
                    break

            if skill_found:
                save_data_file({
                    "jobs_by_country": jobs_by_country,
                    "skills_config": skills_config
                })
                await update.message.reply_text(
                    f"✅ مهارت '{text}' از لیست حذف شد.",
                    reply_markup=skill_management_keyboard()
                )
            else:
                await update.message.reply_text("❌ مهارت مورد نظر در لیست پیدا نشد.")

        # ========== JOB MANAGEMENT ==========
        elif step in ["add_job", "remove_job", "increase_job", "decrease_job"]:
            country = user_data.get("country")
            if not country:
                await update.message.reply_text("❌ کشور مشخص نیست.")
                return

            jobs = jobs_by_country.get(country, [])

            if step == "add_job":
                try:
                    parts = [part.strip() for part in text.split("-")]
                    if len(parts) != 3:
                        await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - لول - ظرفیت")
                        return

                    job_name, level_str, capacity_str = parts
                    level = int(level_str)
                    capacity = int(capacity_str)

                    if any(job.get("name") == job_name for job in jobs):
                        await update.message.reply_text(f"❌ شغل '{job_name}' قبلاً وجود دارد.")
                        return

                    jobs.append({
                        "name": job_name,
                        "level": level,
                        "count": capacity
                    })

                    save_data_file({
                        "jobs_by_country": jobs_by_country,
                        "skills_config": skills_config
                    })

                    await update.message.reply_text(
                        f"✅ شغل '{job_name}' با موفقیت اضافه شد.",
                        reply_markup=admin_back_buttons()
                    )

                except ValueError:
                    await update.message.reply_text("❌ لول و ظرفیت باید عدد باشند.")

            elif step == "remove_job":
                job_to_remove = next((job for job in jobs if job.get("name") == text), None)

                if job_to_remove:
                    jobs.remove(job_to_remove)
                    save_data_file({
                        "jobs_by_country": jobs_by_country,
                        "skills_config": skills_config
                    })
                    await update.message.reply_text(
                        f"✅ شغل '{text}' حذف شد.",
                        reply_markup=admin_back_buttons()
                    )
                else:
                    await update.message.reply_text(f"❌ شغل '{text}' پیدا نشد.")

            elif step in ["increase_job", "decrease_job"]:
                try:
                    parts = [part.strip() for part in text.split("-")]
                    if len(parts) != 2:
                        await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - تعداد")
                        return
            
                    job_name, amount_str = parts
                    amount = int(amount_str)
            
                    country = user_data.get("country")
                    if not country:
                        await update.message.reply_text("❌ کشور مشخص نیست.")
                        return
            
                    # دسترسی امن و مستقیم به لیست واقعی کشور
                    if country not in jobs_by_country:
                        jobs_by_country[country] = []
                    jobs = jobs_by_country[country]  # ← حالا ارجاع واقعی گرفتیم
            
                    job_found = False
                    for job in jobs:
                        if job.get("name") == job_name:
                            old_count = job.get("count", 0)
                            if step == "increase_job":
                                job["count"] = old_count + amount
                            else:
                                job["count"] = max(0, old_count - amount)
                            job_found = True
                            break
            
                    if job_found:
                        save_data_file({
                            "jobs_by_country": jobs_by_country,
                            "skills_config": skills_config
                        })
                        action_text = "افزایش" if step == "increase_job" else "کاهش"
                        await update.message.reply_text(
                            f"✅ ظرفیت شغل '{job_name}' {action_text} یافت.",
                            reply_markup=admin_back_buttons()
                        )
                    else:
                        await update.message.reply_text(f"❌ شغل '{job_name}' پیدا نشد.")
            
                except ValueError:
                    await update.message.reply_text("❌ تعداد باید عدد باشد.")

            # elif step in ["increase_job", "decrease_job"]:
            #     try:
            #         parts = [part.strip() for part in text.split("-")]
            #         if len(parts) != 2:
            #             await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - تعداد")
            #             return

            #         job_name, amount_str = parts
            #         amount = int(amount_str)

            #         job_found = False
            #         for job in jobs:
            #             if job.get("name") == job_name:
            #                 if step == "increase_job":
            #                     job["count"] = job.get("count", 0) + amount
            #                 else:
            #                     job["count"] = max(0, job.get("count", 0) - amount)
            #                 job_found = True
            #                 break

            #         if job_found:
            #             save_data_file({
            #                 "jobs_by_country": jobs_by_country,
            #                 "skills_config": skills_config
            #             })
            #             action_text = "افزایش" if step == "increase_job" else "کاهش"
            #             await update.message.reply_text(
            #                 f"✅ ظرفیت شغل '{job_name}' {action_text} یافت.",
            #                 reply_markup=admin_back_buttons()
            #             )
            #         else:
            #             await update.message.reply_text(f"❌ شغل '{job_name}' پیدا نشد.")

            #     except ValueError:
            #         await update.message.reply_text("❌ تعداد باید عدد باشد.")

        # Clear state at the end
        context.user_data.pop(user_id, None)

    except Exception as e:
        logger.error(f"Error in handle_admin_text_message: {e} | step={step} | text={text}")
        await update.message.reply_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())

# async def cleanup_incomplete_bio_for_user(update, context):
#     """
#     پاکسازی بیو ناقص یک کاربر:
#     - آزاد کردن هشتگ اختصاص داده شده به بیو
#     - افزایش تعداد مشاغل آزاد شده در کشور مربوطه
#     - حذف بیو از حافظه و فایل
#     - ذخیره‌سازی مجدد اطلاعات با تغییرات اعمال شده

#     پارامترها:
#     - update: آبجکت آپدیت تلگرام با اطلاعات کاربر
#     - context: کانتکست اجرایی ربات

#     خروجی:
#     - True اگر عملیات پاکسازی انجام شده باشد
#     - False اگر بیو وجود نداشته یا شرایط پاکسازی نبود
#     """

#     user_id = str(update.effective_user.id)

#     # بارگذاری بیوها و هشتگ‌ها
#     bios_data = load_bios()  # فرض می‌کنیم این تابع بیو + هشتگ ها رو میاره
#     bios_dict = bios_data.get("bios", {})
#     used_hashtags = bios_data.get("used_hashtags", [])

#     user_bio = bios_dict.get(user_id)
#     if not user_bio or user_bio.get("step") == "pending":
#         return False

#     # آزادسازی هشتگ اختصاصی
#     user_tag = user_bio.get("user_id_tag")
#     if user_tag and user_tag in used_hashtags:
#         used_hashtags.remove(user_tag)

#     # حذف بیو از ذخیره بیوها
#     remove_bio_from_storage(int(user_id))

#     # ذخیره تغییرات مربوط به بیوها و هشتگ‌ها
#     save_bios({
#         "bios": bios_dict,
#         "used_hashtags": used_hashtags,
#     })

#     # بارگذاری مشاغل و مهارت‌ها (از فایل/آدرس جدا)
#     jobs_skills_data = load_jobs_skills()  
#     jobs_by_country = jobs_skills_data.get("jobs_by_country", {})
#     skills_config = jobs_skills_data.get("skills_config", {})

#     # آزادسازی شغل کاربر (افزایش count)
#     country = user_bio.get("country")
#     job_name = user_bio.get("job")
#     if country and job_name:
#         jobs = jobs_by_country.get(country, [])
#         for job in jobs:
#             if job.get("name") == job_name:
#                 job["count"] = job.get("count", 0) + 1
#                 break

#     # ذخیره مجدد مشاغل و مهارت‌ها
#     save_jobs_skills({
#         "jobs_by_country": jobs_by_country,
#         "skills_config": skills_config
#     })

#     return True


async def cleanup_incomplete_bio_for_user(update, context):
    user_id = str(update.effective_user.id)

    # بارگذاری بیوها و هشتگ‌ها
    bios_data = load_bios()
    bios_dict = bios_data.get("bios", {})
    used_hashtags = bios_data.get("used_hashtags", [])

    user_bio = bios_dict.get(user_id)
    if not user_bio or user_bio.get("step") == "pending":
        return False

    # آزادسازی هشتگ اختصاصی اگر وجود داشت
    user_tag = user_bio.get("user_id_tag")
    if user_tag and user_tag in used_hashtags:
        used_hashtags.remove(user_tag)

    # آزادسازی شغل کاربر (افزایش count)
    country = user_bio.get("country")
    job_name = user_bio.get("job")
    if country and job_name:
        # بارگذاری داده‌های مشاغل و مهارت‌ها
        data = load_data_file("data.json")
        jobs_by_country = data.get("jobs_by_country", {})
        skills_config = data.get("skills_config", {})

        jobs = jobs_by_country.get(country, [])
        for job in jobs:
            if job.get("name") == job_name:
                print(f"Releasing job: {job_name} in {country}. Old count: {job.get('count', 0)}")
                job["count"] = job.get("count", 0) + 1
                print(f"New count: {job['count']}")
                break
        else:
            print(f"Job not found for {job_name} in {country}")


        # ذخیره مجدد داده‌ها
        save_data("data.json", {
            "jobs_by_country": jobs_by_country,
            "skills_config": skills_config
        })
        data_check = load_data_file("data.json")
        print("Job count after save:", data_check["jobs_by_country"][country])


    # حذف رزرو شغل کاربر
    reservations = load_job_reservations()
    if user_id in reservations:
        del reservations[user_id]
        save_job_reservations(reservations)

    # حذف بیو از دیکشنری
    if user_id in bios_dict:
        del bios_dict[user_id]

    # ذخیره تغییرات بیوها و هشتگ‌ها (بیو پاک شده)
    save_bios({
        "bios": bios_dict,
        "used_hashtags": used_hashtags,
    })

    return True



