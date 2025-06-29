
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_menu, back_button, bio_admin_menu, back_and_home_buttons
from bio_handler import select_country, select_job, ask_bio_fields, handle_skill_navigation, handle_skill_reset, handle_skill_continue, handle_skill_selection
from admin_handler import show_admin_menu, show_admin_job_list, show_admin_skill_list, show_country_jobs, handle_job_actions, handle_skill_actions, handle_bio_approval
from config import RP_PASSWORDS

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

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

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    state = context.user_data.get(user_id, {})
    previous_step = state.get("previous_step")
    
    if previous_step == "country_jobs":
        country = state.get("country")
        if country:
            await show_country_jobs_by_country(update, context, country)
    elif previous_step == "admin_skill_list":
        await show_admin_skill_list(update, context)
    else:
        # Default back to admin menu
        await show_admin_menu(update, context)

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