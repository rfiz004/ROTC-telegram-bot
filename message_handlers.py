import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")

    try:
        # Handle admin password input
        if step == "awaiting_rp_password":
            await handle_rp_password_input(update, context)
        # Handle admin text inputs
        elif step in ["awaiting_skill_name", "removing_skill", "add_job", "remove_job", "increase_job", "decrease_job"]:
            from admin_handler import handle_admin_text_message
            await handle_admin_text_message(update, context)
        else:
            await update.message.reply_text("لطفاً از منو استفاده کنید.")
    except Exception as e:
        logger.error(f"Error in handle_all_messages: {e}")
        await update.message.reply_text("خطایی رخ داد")

async def handle_rp_password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle RP password input"""
    user_id = update.message.from_user.id
    password = update.message.text.strip()

    from config import RP_PASSWORDS, COUNTRY_ADMINS

    # Check passwords
    for role, correct_password in RP_PASSWORDS.items():
        if password == correct_password:
            context.user_data[user_id] = context.user_data.get(user_id, {})
            context.user_data[user_id].update({
                "admin_session": True,
                "admin_role": role,
                "step": None
            })

            # Set admin countries for multi-country admins
            if role in COUNTRY_ADMINS:
                context.user_data[user_id]["admin_countries"] = COUNTRY_ADMINS[role]

            await update.message.reply_text("✅ ورود موفق! به پنل ادمین خوش آمدید.")

            # Redirect to appropriate admin menu
            if role == "bio_admin":
                from admin_handler import show_admin_menu
                await show_admin_menu(update, context)
            elif role in ["multi_admin_1", "multi_admin_2", "multi_admin_3"]:
                from admin_province_handler import show_admin_province_menu
                await show_admin_province_menu(update, context)

            return

    await update.message.reply_text("❌ رمز عبور اشتباه است")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_manager import jobs_by_country, skills_config, save_data
from keyboards import admin_back_buttons, skill_management_keyboard
from config import RP_PASSWORDS
import logging

logger = logging.getLogger(__name__)

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text message inputs"""
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")

    try:
        if step == "awaiting_rp_password":
            # Check RP password and determine role
            from config import RP_PASSWORDS, COUNTRY_ADMINS

            password_role = None
            for role, password in RP_PASSWORDS.items():
                if text == password:
                    password_role = role
                    break

            if password_role:
                # Set admin access based on role
                context.user_data[user_id] = {
                    "admin_access": True,
                    "admin_session": True,
                    "role": password_role,
                    "admin_role": password_role,
                    "step": None  # Clear step
                }

                # Set admin countries for multi-country admins
                if password_role in COUNTRY_ADMINS:
                    context.user_data[user_id]["admin_countries"] = COUNTRY_ADMINS[password_role]

                success_msg = f"✅ خوش آمدید! دسترسی {password_role} فعال شد."
                admin_menu = get_admin_menu_for_role(password_role)

                await update.message.reply_text(success_msg, reply_markup=admin_menu)
            else:
                back_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")
                ]])
                await update.message.reply_text(
                    "❌ رمز عبور نادرست است. لطفاً مجدداً تلاش کنید:",
                    reply_markup=back_keyboard
                )

        elif step in ["awaiting_skill_name", "removing_skill", "add_job", "remove_job", "increase_job", "decrease_job"]:
            # Handle admin operations
            from admin_handler import handle_admin_text_message
            await handle_admin_text_message(update, context)

    except Exception as e:
        logger.error(f"Error in message handler: {e}")
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً مجدداً تلاش کنید.")


def get_admin_menu_for_role(role):
    """Get appropriate admin menu based on role"""
    from keyboards import bio_admin_menu, master_admin_menu, shop_admin_menu, multi_country_admin_menu
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    if role == "master_admin":
        return master_admin_menu()
    elif role == "bio_admin":
        return bio_admin_menu()
    elif role == "shop_admin":
        return shop_admin_menu()
    elif role in ["multi_admin_1", "multi_admin_2", "multi_admin_3"]:
        from config import COUNTRY_ADMINS
        countries = COUNTRY_ADMINS.get(role, [])
        return multi_country_admin_menu(countries)
    else:
        return bio_admin_menu()  # Default fallback

async def handle_rp_password(update: Update, context: ContextTypes.DEFAULT_TYPE, password: str):
    """Handle RP password verification"""
    user_id = update.message.from_user.id

    try:
        role = None
        admin_countries = []

        # Check password against all roles
        for role_name, role_data in RP_PASSWORDS.items():
            if isinstance(role_data, dict):
                # Multi-country admin format
                if password in role_data.get("passwords", []):
                    role = role_name
                    admin_countries = role_data.get("countries", [])
                    break
            elif isinstance(role_data, list):
                # Simple list format
                if password in role_data:
                    role = role_name
                    break

        if role:
            context.user_data[user_id] = {
                "admin_access": True,
                "admin_session": True,
                "role": role,
                "admin_role": role,
                "admin_countries": admin_countries
            }

            try:
                from admin_handler import show_admin_menu
                await show_admin_menu(update, context)
            except ImportError:
                await update.message.reply_text("پنل ادمین در حال حاضر در دسترس نیست.")
        else:
            await update.message.reply_text("❌ کلمه عبور اشتباه است!")
    except Exception as e:
        logger.error(f"Error in handle_rp_password: {e}")
        await update.message.reply_text("❌ خطا در بررسی کلمه عبور")

async def handle_job_management_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle job management text inputs"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")
    country = user_data.get("country")

    try:
        if not country:
            await update.message.reply_text("❌ کشور مشخص نیست.")
            return

        jobs = jobs_by_country.get(country, [])

        if step == "add_job":
            # Parse format: "job_name - level - capacity"
            try:
                parts = [part.strip() for part in text.split("-")]
                if len(parts) != 3:
                    await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - لول - ظرفیت")
                    return

                job_name, level_str, capacity_str = parts
                level = int(level_str)
                capacity = int(capacity_str)

                # Check if job already exists
                if any(job.get("name") == job_name for job in jobs):
                    await update.message.reply_text(f"❌ شغل '{job_name}' قبلاً وجود دارد.")
                    return

                # Add new job
                new_job = {
                    "name": job_name,
                    "level": level,
                    "count": capacity
                }
                jobs.append(new_job)

                save_data({
                    "jobs_by_country": jobs_by_country,
                    "skills_config": skills_config
                })

                await update.message.reply_text(f"✅ شغل '{job_name}' با موفقیت اضافه شد.", reply_markup=admin_back_buttons())

            except ValueError:
                await update.message.reply_text("❌ لول و ظرفیت باید عدد باشند.")
            except Exception as e:
                logger.error(f"Error adding job: {e}")
                await update.message.reply_text("❌ خطا در افزودن شغل.")

        elif step == "remove_job":
            job_to_remove = None
            for job in jobs:
                if job.get("name") == text:
                    job_to_remove = job
                    break

            if job_to_remove:
                jobs.remove(job_to_remove)
                save_data({
                    "jobs_by_country": jobs_by_country,
                    "skills_config": skills_config
                })
                await update.message.reply_text(f"✅ شغل '{text}' حذف شد.", reply_markup=admin_back_buttons())
            else:
                await update.message.reply_text(f"❌ شغل '{text}' پیدا نشد.")

        elif step in ["increase_job", "decrease_job"]:
            # Parse format: "job_name - amount"
            try:
                parts = [part.strip() for part in text.split("-")]
                if len(parts) != 2:
                    await update.message.reply_text("❌ فرمت اشتباه! فرمت صحیح: نام شغل - تعداد")
                    return

                job_name, amount_str = parts
                amount = int(amount_str)

                job_found = False
                for job in jobs:
                    if job.get("name") == job_name:
                        if step == "increase_job":
                            job["count"] = job.get("count", 0) + amount
                        else:  # decrease_job
                            job["count"] = max(0, job.get("count", 0) - amount)
                        job_found = True
                        break

                if job_found:
                    save_data({
                        "jobs_by_country": jobs_by_country,
                        "skills_config": skills_config
                    })
                    action_text = "افزایش" if step == "increase_job" else "کاهش"
                    await update.message.reply_text(f"✅ ظرفیت شغل '{job_name}' {action_text} یافت.", reply_markup=admin_back_buttons())
                else:
                    await update.message.reply_text(f"❌ شغل '{job_name}' پیدا نشد.")

            except ValueError:
                await update.message.reply_text("❌ تعداد باید عدد باشد.")
            except Exception as e:
                logger.error(f"Error modifying job: {e}")
                await update.message.reply_text("❌ خطا در تغییر ظرفیت شغل.")

        context.user_data.pop(user_id, None)
    except Exception as e:
        logger.error(f"Error in handle_job_management_text: {e}")
        await update.message.reply_text("❌ خطا در پردازش درخواست.", reply_markup=admin_back_buttons())

async def handle_skill_management_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle skill management text inputs"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")
    skill_type = user_data.get("skill_type", "normal")

    try:
        if step == "awaiting_skill_name":
            # Add skill to appropriate list
            if skill_type not in skills_config:
                skills_config[skill_type] = []

            if text in skills_config[skill_type]:
                await update.message.reply_text(f"❌ مهارت '{text}' قبلاً در لیست وجود دارد.")
            else:
                skills_config[skill_type].append(text)
                save_data({"jobs_by_country": jobs_by_country, "skills_config": skills_config})
                await update.message.reply_text(f"✅ مهارت '{text}' به لیست {'عادی' if skill_type == 'normal' else 'خاص'} اضافه شد.", reply_markup=skill_management_keyboard())

            context.user_data.pop(user_id, None)

        elif step == "removing_skill":
            # Remove skill from appropriate list
            skill_found = False
            for skill_list_type in ["normal", "special"]:
                if text in skills_config.get(skill_list_type, []):
                    skills_config[skill_list_type].remove(text)
                    skill_found = True
                    break

            if skill_found:
                save_data({"jobs_by_country": jobs_by_country, "skills_config": skills_config})
                await update.message.reply_text(f"✅ مهارت '{text}' حذف شد.", reply_markup=skill_management_keyboard())
            else:
                await update.message.reply_text(f"❌ مهارت '{text}' یافت نشد.")

            context.user_data.pop(user_id, None)
    except Exception as e:
        logger.error(f"Error in handle_skill_management_text: {e}")
        await update.message.reply_text("❌ خطا در مدیریت مهارت")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages and route to appropriate handlers"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    flow_type = user_data.get("flow_type")
    step = user_data.get("step")
    state = user_data.get("state")

    logger.info(f"Text router - User {user_id}: flow_type={flow_type}, state={state}, step={step}")

    try:
        # Route to specific handlers based on flow type and step
        # Transfer items input
        if step == "awaiting_transfer_items_input":
            from transfer_handler import handle_transfer_items_input
            if await handle_transfer_items_input(update, context):
                return

        # Admin province editing
        if step and step.startswith("awaiting_province_"):
            from admin_province_handler import handle_province_edit_input
            if await handle_province_edit_input(update, context):
                return

        # Bio editing
        if step and step.startswith("awaiting_bio_"):
            from bio_handler import handle_bio_text_input
            if await handle_bio_text_input(update, context):
                return

        # Shop item management
        if step and step.startswith("awaiting_shop_"):
            from admin_province_handler import handle_shop_item_text_input
            if await handle_shop_item_text_input(update, context):
                return

        # Country management flow
        if flow_type == "country_management":
            from country_handler import handle_user_text
            await handle_user_text(update, context)
            return

        # Bio management flow
        if flow_type == "bio_management":
            from bio_handler import handle_user_text
            await handle_user_text(update, context)
            return

        # Default fallback
        await update.message.reply_text(
            "❓ متوجه نشدم. لطفاً از منوهای ربات استفاده کنید.",
            reply_markup=start_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in text message handling: {e}")
        await update.message.reply_text("❌ خطا در پردازش پیام")

async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages"""
    user_id = update.message.from_user.id
    user_data = context.user_data.get(user_id, {})
    step = user_data.get("step")

    logger.info(f"Photo handler - User {user_id}: step={step}")

    try:
        # Shop item image upload
        if step == "awaiting_shop_item_image":
            from admin_province_handler import handle_shop_item_image
            await handle_shop_item_image(update, context)
            return

        # Bio photo upload
        if step == "awaiting_bio_photo":
            from bio_handler import handle_bio_photo_upload
            await handle_bio_photo_upload(update, context)
            return

        # Default photo message response
        await update.message.reply_text("لطفاً ابتدا از منوهای ربات گزینه مربوطه را انتخاب کنید.")

    except Exception as e:
        logger.error(f"Error in photo handling: {e}")
        await update.message.reply_text("❌ خطا در پردازش تصویر")