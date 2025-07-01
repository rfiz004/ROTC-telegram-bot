from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from keyboards import main_menu, back_button, bio_admin_menu, back_and_home_buttons, admin_back_buttons
from bio_handler import select_country, select_job, ask_bio_fields, handle_skill_navigation, handle_skill_reset, handle_skill_continue, handle_skill_selection
from admin_handler import show_admin_menu, show_admin_job_list, show_admin_skill_list, show_country_jobs, handle_job_actions, handle_skill_actions, handle_bio_approval
from config import RP_PASSWORDS

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "bio":
            await select_country(update, context)
        elif data == "manage_country":
            await query.message.edit_text("این بخش بعداً اضافه می‌شه 🏗", reply_markup=back_button())
        elif data == "rp_settings":
            await query.message.edit_text("🔐 لطفاً رمز ورود به تنظیمات رو بفرست:", reply_markup=back_button())
            context.user_data[query.from_user.id] = {"step": "awaiting_rp_password"}
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
            # Clear user state when going back to main
            user_id = query.from_user.id
            context.user_data.pop(user_id, None)
            await query.message.edit_text("درود! 👋\n به راهنمای آرپی R.O.T.C خوش اومدی چه کمکی میتونم بهت بکنم؟", reply_markup=main_menu())
        elif data == "back_to_admin_menu":
            await show_admin_menu(update, context)
        elif data == "back_to_previous":
            await handle_back_navigation(update, context)
        elif data == "admin_job_list":
            await show_admin_job_list(update, context)
        elif data == "admin_skill_list":
            await show_admin_skill_list(update, context)
        elif data == "add_skill":
            await handle_skill_actions(update, context)
        elif data == "remove_skill":
            await handle_skill_actions(update, context)
        elif data.startswith("skill_type_"):
            user_id = query.from_user.id
            skill_type = data.split("_")[-1]  
            context.user_data[user_id] = {
                "step": "awaiting_skill_name",
                "skill_type": skill_type,
                "previous_step": "admin_skill_list"
            }
            await query.message.edit_text(f"📝 اسم مهارت { 'عادی' if skill_type == 'normal' else 'خاص' } رو بفرست:",
                                          reply_markup=admin_back_buttons())
    except BadRequest as e:
        if "Message is not modified" in str(e):
            # Message content is the same, ignore the error
            pass
        else:
            raise e

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state = context.user_data.get(user_id, {})
    current_step = user_state.get("step")

    if query.data == "back_to_previous":
        # If user is in job selection, go back to country selection
        if current_step == "selecting_job":
            # Assuming country_jobs_keyboard is defined elsewhere and correctly returns the country job options
            from bio_handler import country_jobs_keyboard  # Import here to avoid circular import issues

            context.user_data[user_id] = {"step": "selecting_country"}
            try:
                await query.message.edit_text("برای کدوم کشور می‌خوای بیو بدی؟", reply_markup=country_jobs_keyboard())
            except BadRequest as e:
                if "Message is not modified" in str(e):
                    pass
                else:
                    raise e
        else:
            await query.message.edit_text(
                "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
                reply_markup=main_menu()
            )
    elif query.data == "back_to_main":
        await query.message.edit_text(
            "درود! 👋\nبه راهنمای آرپی R.O.T.C خوش اومدی، چه کمکی می‌تونم بهت بکنم؟",
            reply_markup=main_menu()
        )
    elif query.data == "back_to_admin_menu":
        await query.message.edit_text("با حضورتون منورمون کردین😔✨",
                                      reply_markup=bio_admin_menu())

async def show_country_jobs_by_country(update: Update, context: ContextTypes.DEFAULT_TYPE, country: str):
    from admin_handler import show_country_jobs
    # Simulate the callback data for show_country_jobs
    update.callback_query.data = f"manage_jobs_{country}"
    await show_country_jobs(update, context)

async def handle_password_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = context.user_data.get(user_id, {})

    if state.get("step") == "awaiting_rp_password":
        if text == RP_PASSWORDS["main_admin"]:
            await update.message.reply_text("ها چیه چی میخواستی باشه؟؟")
        elif text == RP_PASSWORDS["bio_admin"]:
            await update.message.reply_text("خوش اومدی سیسی کیوت (امیر و علی اگه اومدن گمشن)", reply_markup=bio_admin_menu())
        elif text == RP_PASSWORDS["shop_admin"]:
            await update.message.reply_text("اینجا فعلا صاحاب نداره")
        else:
            await update.message.reply_text("اوپس رمز اشتباهه، سیسیا قشنگای من اگه یادتون نیست رمزو بیاین بگم بهتون \n غیر ادمینا (و ادمین اصلیا) گمشن ممنون")
        context.user_data.pop(user_id, None)