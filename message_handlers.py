
from telegram import Update
from telegram.ext import ContextTypes
from data_manager import jobs_by_country, skills_list, save_data
from keyboards import bio_admin_menu
from bio_handler import collect_bio
from callback_handlers import handle_password_message

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = context.user_data.get(user_id, {})
    step = state.get("step")

    if state.get("step") == "awaiting_rp_password":
        await handle_password_message(update, context)
    elif state.get("step") == "adding_skill":
        skill = update.message.text.strip()

        if skill in skills_list:
            await update.message.reply_text("⚠️ خدایی دوتا مهارت یکسان و میخوای تو کجات کنی؟؟ یکی دیگه انتخاب کن")
            # Don't clear user_data, keep them in the same step
        else:
            skills_list.append(skill)
            save_data({
                "jobs_by_country": jobs_by_country,
                "skills_list": skills_list
            })
            await update.message.reply_text("✅ مهارت اضافه شد.", reply_markup=bio_admin_menu())
            context.user_data.pop(user_id, None)

    elif state.get("step") == "removing_skill":
        skill_to_remove = update.message.text.strip()
        if skill_to_remove in skills_list:
            skills_list.remove(skill_to_remove)
            save_data({
              "jobs_by_country": jobs_by_country,
              "skills_list": skills_list
            })
            await update.message.reply_text("❌ مهارت حذف شد.", reply_markup=bio_admin_menu())
            context.user_data.pop(user_id, None)
        else:
            await update.message.reply_text("⚠️ مهارت پیدا نشد. دوباره تلاش کن:")
            # Don't clear user_data, keep them in the same step
        
    elif step == "add_job":
        parts = update.message.text.split("-")
        if len(parts) != 3:
            await update.message.reply_text("❌ فرمت اشتباهه. درست بنویس: اسم شغل - لولش - تعدادی که بیو میخوایم براش")
            return  # Don't clear user_data, keep them in the same step
        try:
            name, level, count = [x.strip() for x in update.message.text.split("-")]
            level = int(level)
            count = int(count)
            country = state["country"]
            
            # Check if job already exists
            existing_job = next((j for j in jobs_by_country[country] if j["name"] == name), None)
            if existing_job:
                await update.message.reply_text("⚠️ این شغل قبلاً وجود داره. نام دیگری انتخاب کن:")
                return  # Don't clear user_data
                
            jobs_by_country[country].append({"name": name, "level": level, "count": count})
            save_data({
                "jobs_by_country": jobs_by_country,
                "skills_list": skills_list
            })
            await update.message.reply_text("✅ شغل اضافه شد.", reply_markup=bio_admin_menu())
            context.user_data.pop(user_id, None)
        except ValueError:
            await update.message.reply_text("❌ لول و تعداد باید عدد باشن. دوباره تلاش کن:")
            # Don't clear user_data, keep them in the same step
        except Exception:
            await update.message.reply_text("❌ درست بنویس دیگه ببین اینجوری: اسم شغل - لولش - تعدادی که بیو میخوایم براش")
            # Don't clear user_data, keep them in the same step

    elif step == "remove_job":
        name = update.message.text.strip()
        country = state["country"]
        jobs = jobs_by_country[country]
        
        # Check if job exists
        job_exists = any(j["name"] == name for j in jobs)
        if not job_exists:
            await update.message.reply_text("⚠️ شغل پیدا نشد. دوباره تلاش کن:")
            return  # Don't clear user_data
            
        jobs_by_country[country] = [j for j in jobs if j["name"] != name]
        save_data({
            "jobs_by_country": jobs_by_country,
            "skills_list": skills_list
        })
        await update.message.reply_text("❌ شغل حذف شد.", reply_markup=bio_admin_menu())
        context.user_data.pop(user_id, None)

    elif step == "increase_job":
        try:
            parts = update.message.text.split("-")
            if len(parts) != 2:
                await update.message.reply_text("❌ فرمت اشتباهه. بنویس: نام شغل - تعداد افزایش")
                return  # Don't clear user_data
                
            name, amount = [x.strip() for x in parts]
            amount = int(amount)
            
            if amount <= 0:
                await update.message.reply_text("❌ تعداد افزایش باید بیشتر از صفر باشه:")
                return  # Don't clear user_data
                
            country = state["country"]
            job = next((j for j in jobs_by_country[country] if j["name"] == name), None)
            
            if not job:
                await update.message.reply_text("⚠️ شغل پیدا نشد. دوباره تلاش کن:")
                return  # Don't clear user_data
                
            job["count"] += amount
            save_data({
              "jobs_by_country": jobs_by_country,
              "skills_list": skills_list
            })
            await update.message.reply_text("✅ ظرفیت بیشتر شد.", reply_markup=bio_admin_menu())
            context.user_data.pop(user_id, None)
        except ValueError:
            await update.message.reply_text("❌ تعداد باید عدد باشه. دوباره تلاش کن:")
            # Don't clear user_data
        except Exception:
            await update.message.reply_text("❌ فرمت اشتباهه. بنویس: نام شغل - تعداد افزایش")
            # Don't clear user_data

    elif step == "decrease_job":
        try:
            parts = update.message.text.split("-")
            if len(parts) != 2:
                await update.message.reply_text("❌ فرمت اشتباهه. بنویس: نام شغل - تعداد کاهش")
                return  # Don't clear user_data
                
            name, amount = [x.strip() for x in parts]
            amount = int(amount)
            
            if amount <= 0:
                await update.message.reply_text("❌ تعداد کاهش باید بیشتر از صفر باشه:")
                return  # Don't clear user_data
                
            country = state["country"]
            job = next((j for j in jobs_by_country[country] if j["name"] == name), None)
            
            if not job:
                await update.message.reply_text("⚠️ شغل پیدا نشد. دوباره تلاش کن:")
                return  # Don't clear user_data
                
            job["count"] = max(0, job["count"] - amount)
            save_data({
                "jobs_by_country": jobs_by_country,
                "skills_list": skills_list
            })
            await update.message.reply_text("✅ ظرفیت کم شد.", reply_markup=bio_admin_menu())
            context.user_data.pop(user_id, None)
        except ValueError:
            await update.message.reply_text("❌ تعداد باید عدد باشه. دوباره تلاش کن:")
            # Don't clear user_data
        except Exception:
            await update.message.reply_text("❌ فرمت اشتباهه. بنویس: نام شغل - تعداد کاهش")
            # Don't clear user_data

    else:
        await collect_bio(update, context)
