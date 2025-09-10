"""
Province handler module - handles province management functionality
"""
import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler
from keyboards import back_and_home_buttons



PROVINCE_FOLDER = "provinces"  # مسیر فولدر استان ‌ها

logger = logging.getLogger(__name__)

# async def show_province_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Show detailed province information"""
#     query = update.callback_query
#     await query.answer()

#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     try:
#         country = user_data.get("country", "نامشخص")
#         province = user_data.get("province", "نامشخص")

#         # Basic province info display
#         info_text = f"""🏰 **اطلاعات استان {province}**
# 🌍 کشور: {country}

# 📊 وضعیت کلی:
# • جمعیت: در حال بروزرسانی
# • اقتصاد: پایدار
# • امنیت: عالی

# 💰 منابع موجود:
# • طلا: در حال بروزرسانی
# • نقره: در حال بروزرسانی
# • مس: در حال بروزرسانی

# 🏗️ ساختمان‌ها:
# • در حال بروزرسانی

# ⚔️ نیروی نظامی:
# • در حال بروزرسانی"""

#         await query.edit_message_text(info_text, reply_markup=back_and_home_buttons())
#     except Exception as e:
#         logger.error(f"Error showing province info: {e}")
#         await query.edit_message_text("❌ خطا در نمایش اطلاعات استان", reply_markup=back_and_home_buttons())

async def edit_province_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit province data"""
    # Placeholder implementation
    await update.message.reply_text("ویرایش اطلاعات استان در حال حاضر در دسترس نیست.")

async def show_province_economy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show province economy details"""
    # Placeholder implementation
    await update.callback_query.edit_message_text("نمایش اقتصاد استان در حال حاضر در دسترس نیست.")

async def show_province_military(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show province military details"""
    # Placeholder implementation
    await update.callback_query.edit_message_text("نمایش نیروی نظامی استان در حال حاضر در دسترس نیست.")


import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import back_and_home_buttons
import logging

logger = logging.getLogger(__name__)

def load_province_data(country, province):
    """Load province data from JSON file"""
    try:
        # Normalize the province name
        normalized_province = province.strip()

        # Try different filename formats
        filename_variations = [
            f"provinces/{country}_{normalized_province.replace(' ', '_')}.json",
            f"provinces/{country}_{normalized_province}.json",
            f"provinces/{country}_{province}.json"
        ]

        for filename in filename_variations:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"Successfully loaded province data from: {filename}")
                return data

        # If no file found, log available files for debugging
        if os.path.exists("provinces"):
            available_files = [f for f in os.listdir("provinces") if f.startswith(f"{country}_")]
            logger.warning(f"Province file not found for {country}_{normalized_province}. Available files: {available_files}")

        return None
    except Exception as e:
        logger.error(f"Error loading province data for {country}/{province}: {e}")
        return None

# def load_central_province_data():
#     """Load province data from central provinces.json file"""
#     province_file = "provinces.json"
#     if not os.path.exists(province_file):
#         # Create default structure
#         default_data = {
#             "countries": {
#                 "Aldemar": {
#                     "capital": "Marevenport",
#                     "provinces": {
#                         "Marevenport": {
#                             "mines": {"Copper mine": 10000},
#                             "wealth": 0,
#                             "population": 30000,
#                             "tax": 0,
#                             "popularity": 70,
#                             "army": {
#                                 "کماندار": 2000,
#                                 "شمشیرزن": 1500,
#                                 "نیزه دار": 1000,
#                                 "سواره نظام": 500
#                             },
#                             "castle": [
#                                 "یک دیوار یک لایه دور شهر",
#                                 "4 برج در چهار گوشه",
#                                 "یک دروازه لولایی"
#                             ],
#                             "structures": [],
#                             "weapons": [],
#                             "misc": [],
#                             "economic_items": {
#                                 "گندم": 0, "گوشت": 0, "ماهی": 0, "مرغ": 0,
#                                 "میوه": 0, "فولاد": 0, "شیشه": 0, "سنگ": 0,
#                                 "چوب": 0, "جواهر": 0, "پنبه": 0, "پارچه": 0,
#                                 "چرم": 0, "شراب": 0
#                             },
#                             "economic_structures": {
#                                 "ماهیگیری": 0,
#                                 "جواهرسازی": 0,
#                                 "کارخونه پارچه": 0,
#                                 "کارخونه شیشه": 0
#                             }
#                         }
#                     }
#                 }
#             }
#         }
#         save_central_province_data(default_data)
#         return default_data

#     try:
#         with open(province_file, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception as e:
#         logger.error(f"Error loading central province data: {e}")
#         return {"countries": {}}

def save_central_province_data(data):
    """Save province data to central JSON file"""
    try:
        with open("provinces.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving province data: {e}")
        return False

def save_province_data(country, province, data):
    """Save province data to individual JSON file"""
    try:
        province_file = f"provinces/{country}_{province.replace(' ', '_')}.json"
        os.makedirs("provinces", exist_ok=True)
        with open(province_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving individual province data: {e}")
        return False

def create_new_province(country, province):
    """Create a new province with default values"""
    province_data = {
        "country": country,
        "province": province,
        "mines": {"Copper mine": 10000},
        "wealth": 0,
        "population": 30000,
        "tax": 0,
        "popularity": 70,
        "total_army": 5000,
        "army": {
            "کماندار": 2000,
            "شمشیرزن": 1500,
            "نیزه دار": 1000,
            "سواره نظام": 500
        },
        "castle": [
            "یک دیوار یک لایه دور شهر",
            "4 برج در چهار گوشه",
            "یک دروازه لولایی"
        ],
        "structures": [],
        "weapons": [],
        "misc": [],
        "economic_items": {
            "گندم": 0, "گوشت": 0, "ماهی": 0, "مرغ": 0,
            "میوه": 0, "فولاد": 0, "شیشه": 0, "سنگ": 0,
            "چوب": 0, "جواهر": 0, "پنبه": 0, "پارچه": 0,
            "چرم": 0, "شراب": 0
        },
        "economic_structures": {
            "ماهیگیری": 0,
            "جواهرسازی": 0,
            "کارخونه پارچه": 0,
            "کارخونه شیشه": 0
        }
    }

def save_province_data(country, province, data):
    filename = f"{country}_{province}".replace(" ", "_") + ".json"
    filepath = os.path.join(PROVINCE_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_country_provinces(country_name):
    """Get all provinces for a country"""
    try:
        # First try to load from countries.json
        with open("countries.json", 'r', encoding='utf-8') as f:
            countries_data = json.load(f)

        provinces = countries_data.get("countries_areas", {}).get(country_name, [])
        return provinces
    except Exception as e:
        logger.error(f"Error loading country provinces: {e}")
        return []

# async def show_province_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Show province information in exact required format"""
#     query = update.callback_query
#     await query.answer()

#     user_id = query.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     country = user_data.get("country", "نامشخص")
#     province = user_data.get("province", "نامشخص")

#     # Push current state for back navigation
#     from callback_handlers import push_navigation_state
#     push_navigation_state(user_data, "country_menu")

#     province_data = load_province_data(country, province)
#     if not province_data:
#         province_data = create_new_province(country, province)

#     # Format exactly as requested
#     text = f"{country} : {province} \n\n"

#     # Mine section
#     mines = province_data.get("mines", province_data.get("mine", {"Copper mine": 10000}))
#     text += "⬤ معدن : \n"
#     for mine_name, amount in mines.items():
#         text += f"{mine_name} : {amount:,}𓆩𐊧𓆪\n"
#     text += "\n"

#     # Wealth
#     wealth = province_data.get("wealth", 0)
#     text += f"⬤ ثروت : {wealth:,}𓆩𐊧𓆪\n\n"

#     # Population
#     population = province_data.get("population", 30000)
#     text += f"⬤ جمیعت : {population:,} نفر\n\n"

#     # Tax
#     tax = province_data.get("tax", 0)
#     text += f"⬤ مالیات : {tax}\n\n"

#     # Popularity
#     popularity = province_data.get("popularity", 70)
#     text += f"⬤ محبوبیت : {popularity} \n\n"

#     # Army
#     total_army = province_data.get("total_army", 5000)
#     text += f"⬤ تعداد کل سرباز : {total_army:,}\n"
#     army = province_data.get("army", {})
#     army_mapping = {
#         "کماندار": "کماندار",
#         "شمشیرزن": "شمشیرزن", 
#         "نیزه دار": "نیزه دار",
#         "سواره نظام": "سواره نظام",
#         "archer": "کماندار",
#         "swordsman": "شمشیرزن",
#         "spearman": "نیزه دار", 
#         "cavalry": "سواره نظام"
#     }

#     for unit_key, count in army.items():
#         unit_name = army_mapping.get(unit_key, unit_key)
#         text += f"✧ {unit_name} : {count:,}\n"
#     text += "\n"

#     # Castle
#     text += "⬤ قلعه :\n"
#     castle = province_data.get("castle", [])
#     if castle:
#         for castle_item in castle:
#             text += f"✧ {castle_item} \n"
#     else:
#         text += "✧ \n"
#     text += "\n"

#     # Structures
#     text += "⬤ سازه ها : \n"
#     structures = province_data.get("structures", [])
#     if structures:
#         for struct in structures:
#             text += f"✧ {struct}\n"
#     else:
#         text += "✧\n"
#     text += "\n"

#     # Weapons
#     text += "⬤ سلاح : \n"
#     weapons = province_data.get("weapons", [])
#     if weapons:
#         for weapon in weapons:
#             text += f"✧ {weapon}\n"
#     else:
#         text += "✧\n"
#     text += "\n"

#     # Miscellaneous
#     text += "⬤ متفرقه : \n"
#     misc = province_data.get("misc", [])
#     if misc:
#         for item in misc:
#             text += f"✧ {item}\n"
#     else:
#         text += "✧\n"
#     text += "\n"

#     # Economic items
#     text += "⬤ اقلام اقتصادی:\n"
#     economic_items = province_data.get("economic_items", {})
#     for item_name in ["گندم", "گوشت", "ماهی", "مرغ", "میوه", "فولاد", "شیشه", "سنگ", "چوب", "جواهر", "پنبه", "پارچه", "چرم", "شراب"]:
#         amount = economic_items.get(item_name, 0)
#         text += f"✧ {item_name} : {amount}\n"
#     text += "\n"

#     # Economic structures
#     text += "⬤ سازه‌های اقتصادی:\n\n"
#     economic_structures = province_data.get("economic_structures", {})

#     fishing = economic_structures.get("ماهیگیری", economic_structures.get("fishing", 0))
#     jewelry = economic_structures.get("جواهرسازی", economic_structures.get("jewelry", 0))  
#     textile = economic_structures.get("کارخونه پارچه", economic_structures.get("textile", 0))
#     glass = economic_structures.get("کارخونه شیشه", economic_structures.get("glass", 0))

#     text += f"✧ تعداد ماهیگیری : {fishing} = {fishing} ماهی در هفته\n"
#     text += f"✧ تعداد جواهرسازی : {jewelry} = {jewelry} جواهر در هفته \n"
#     text += f"✧ تعداد کارخونه پارچه : {textile} = {textile} پارچه در هفته \n"
#     text += f"✧ تعداد کارخونه شیشه : {glass} = {glass} شیشه در هفته"

#     await query.edit_message_text(text, reply_markup=back_and_home_buttons())


async def show_province_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show province information completely dynamically"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    country = user_data.get("country", "نامشخص")
    province = user_data.get("province", "نامشخص")

    from callback_handlers import push_navigation_state
    push_navigation_state(user_data, "country_menu")

    province_data = load_province_data(country, province)
    if not province_data:
        province_data = create_new_province(country, province)

    # Start formatting
    text = f"{country} : {province} \n\n"

    def format_number(val):
        return f"{val:,}" if isinstance(val, int) else str(val)

    def format_section(title, data):
        out = f"⬤ {title}:\n"
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (int, float, str)):
                    out += f"✧ {k} : {format_number(v)}\n"
                elif isinstance(v, dict):
                    # For structured info like economic structures
                    count = v.get("count", 0)
                    product = v.get("product", "نامشخص")
                    weekly = v.get("weekly_output", 0)
                    out += f"✧ تعداد {k} : {count} : {weekly} {product} در هفته\n"
        elif isinstance(data, list):
            if data:
                for item in data:
                    out += f"✧ {item}\n"
            else:
                out += "✧\n"
        else:
            out += f"✧ {format_number(data)}\n"
        out += "\n"
        return out

    # Display all fields dynamically
     # محاسبه مجموع سربازها از بخش army
    if "army" in province_data and isinstance(province_data["army"], dict):
        province_data["total_army"] = sum(province_data["army"].values())
    for key, value in province_data.items():
        if key in ("country", "province", "structure_productions"):
            continue  # already displayed at top

        title_map = {
            "mines": "معدن",
            "wealth": "ثروت",
            "population": "جمیعت",
            "tax": "مالیات",
            "popularity": "محبوبیت",
            "total_army": "تعداد کل سرباز",
            "army": "ارتش",
            "castle": "قلعه",
            "structures": "سازه ها",
            "weapons": "سلاح",
            "misc": "متفرقه",
            "economic_items": "اقلام اقتصادی",
            "economic_structures": "سازه‌های اقتصادی"
        }

        label = title_map.get(key, key)
        section_text = format_section(label, value)
        text += section_text
    
    await query.edit_message_text(text, reply_markup=back_and_home_buttons())




async def show_economy_overview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show economic overview with weekly calculations in exact requested format"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    country = user_data.get("country", "نامشخص")
    province = user_data.get("province", "نامشخص")

    province_data = load_province_data(country, province)
    if not province_data:
        from province_handler import create_new_province
        province_data = create_new_province(country, province)

    # Determine if this province is capital (first province in list is capital)
    try:
        with open("countries.json", "r", encoding="utf-8") as f:
            countries_data = json.load(f)
        provinces_list = countries_data.get("countries_areas", {}).get(country, [])
        is_capital = len(provinces_list) > 0 and province == provinces_list[0]
    except:
        is_capital = False

    # Calculate weekly economics
    from admin_province_handler import calculate_weekly_income, calculate_weekly_production, calculate_tax_effects, calculate_weekly_food_consumption
    
    population = province_data.get("population", 0)
    
    # Calculate weekly income
    mine_income, mine_details = calculate_weekly_income(province_data)
    
    # Calculate production (only if population > 0)
    if population > 0:
        production_results, prod_details = calculate_weekly_production(province_data)
    else:
        production_results = {}
    
    # Calculate tax effects with correct capital status
    tax_income, popularity_change = calculate_tax_effects(province_data, is_capital=is_capital)
    
    # Calculate food consumption
    if population > 0:
        food_consumption = calculate_weekly_food_consumption(population)
    else:
        food_consumption = {}
    
    # Format display in exact requested format
    text = f"اقتصاد هفتگی:\n\n"
    
    # Mine and tax income
    text += "معدن:\n"
    if mine_income > 0:
        text += f"{mine_income:,} طلا\n"
    else:
        text += "0\n"
    
    text += "مالیات:\n"
    if tax_income > 0:
        text += f"{tax_income:,} طلا\n"
    else:
        text += "0\n"
    
    text += "\n"
    
    # Popularity effects
    text += "تاثیرات محبوبیت: "
    if popularity_change > 0:
        text += f"(+{popularity_change})\n"
    elif popularity_change < 0:
        text += f"({popularity_change})\n"
    else:
        text += "(0)\n"
    
    text += "\n"
    
    # Production
    text += "تولیدات:\n"
    if production_results and population > 0:
        for item, amount in production_results.items():
            if item == "ماهی":
                text += f"ماهیگیری: {amount} ماهی\n"
            elif item == "جواهر":
                text += f"جواهرسازی: {amount} جواهر\n"
            elif item == "پارچه":
                text += f"کارخونه پارچه: {amount} پارچه\n"
            elif item == "شیشه":
                text += f"کارخونه شیشه: {amount} شیشه\n"
            else:
                text += f"{item}: {amount}\n"
    else:
        text += "0\n"
    
    text += "\n"
    
    # Population consumption
    text += f"مصرف جمعیت ({population:,} نفر):\n"
    if food_consumption and population > 0:
        for food_item, consumption in food_consumption.items():
            text += f"{abs(consumption)} {food_item}\n"
    else:
        text += "0\n"

    from keyboards import back_and_home_buttons
    await query.edit_message_text(text, reply_markup=back_and_home_buttons())

def format_province_display(province_data):
    """Format province data for display - compatibility function"""
    return f"استان: {province_data.get('province', 'نامشخص')}"



# COUNTRIES_FILE = "countries.json"

# def find_country_by_province(province_name: str) -> str | None:
#     if not os.path.exists(COUNTRIES_FILE):
#         return None

#     with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     countries_areas = data.get("countries_areas", {})

#     for country, provinces in countries_areas.items():
#         if province_name in provinces:
#             return country
#     return None


# PROVINCES_PATH = "provinces"
# ECONOMIC_PATH = "EconomicItems"

# async def show_grain_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.callback_query.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     country = user_data.get("selected_country")
#     province = user_data.get("selected_province")
#     print(f"country: {country}")
#     print(f"province: {province}")

#     if not province:
#         await update.callback_query.edit_message_text("⛔ ابتدا استان را انتخاب کنید.")
#         return

#     # بارگذاری فایل جمعیت
#     # province_file = os.path.join(PROVINCES_PATH, f"{province}.json")
#     province_file = os.path.join(PROVINCES_PATH, f"{country}_{province}.json")
#     economic_file = os.path.join(ECONOMIC_PATH, f"{province}.json")

#     if not os.path.exists(province_file) or not os.path.exists(economic_file):
#         await update.callback_query.edit_message_text("⛔ فایل‌های موردنیاز پیدا نشد.")
#         return

#     with open(province_file, "r", encoding="utf-8") as f:
#         province_data = json.load(f)

#     with open(economic_file, "r", encoding="utf-8") as f:
#         economic_data = json.load(f)

#     population = province_data.get("population", 0)
#     grain_priority = economic_data.get("grain_priority", [])
#     grains = economic_data.get("grains", {})

#     if not grain_priority:
#         await update.callback_query.edit_message_text("⛔ اولویت غلات تنظیم نشده است.")
#         return

#     if not grains:
#         await update.callback_query.edit_message_text("⛔ درصد مصرف غلات تنظیم نشده است.")
#         return

#     # محاسبه تخمینی کاهش مصرف (مثال فرضی)
#     total_reduction = 0
#     details = []
#     for grain in grain_priority:
#         percentage = grains.get(grain, 100)
#         reduction = 100 - percentage  # درصد کاهش مصرف
#         total_reduction += reduction
#         details.append(f"{grain}: کاهش {reduction}%")

#     avg_reduction = total_reduction / len(grain_priority) if grain_priority else 0
#     estimated_reduction = (population * avg_reduction) / 100  # فرضی برای نمایش

#     msg = (
#         f"👥 جمعیت استان: {population}\n"
#         f"📉 کاهش مصرف میانگین: {avg_reduction:.1f}%\n"
#         f"↘️ تخمین جمعیت کمتر تغذیه‌شده: {int(estimated_reduction)} نفر\n\n"
#         "جزئیات:\n" + "\n".join(details)
#     )

#     await update.callback_query.edit_message_text(msg)


# COUNTRIES_FILE = "countries.json"
# PROVINCES_PATH = "provinces"   # مسیر پوشه استان‌ها را درست کن
# ECONOMIC_PATH = "EconomicItems"        # مسیر پوشه اقتصادی‌ها

# async def show_grain_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.callback_query.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     province = user_data.get("selected_province")

#     if not province:
#         await update.callback_query.edit_message_text("⛔ ابتدا استان را انتخاب کنید.")
#         return

#     # تابع کمکی برای پیدا کردن کشور از روی استان
#     def find_country_by_province(province_name: str) -> str | None:
#         if not os.path.exists(COUNTRIES_FILE):
#             return None
#         with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         countries_areas = data.get("countries_areas", {})
#         for country, provinces in countries_areas.items():
#             if province_name in provinces:
#                 return country
#         return None

#     country = find_country_by_province(province)

#     if not country:
#         await update.callback_query.edit_message_text("⛔ کشور استان پیدا نشد.")
#         return

#     print(f"country: {country}")
#     print(f"province: {province}")
    
#     province_file = os.path.join(PROVINCES_PATH, f"{country}_{province}.json")
#     economic_file = os.path.join(ECONOMIC_PATH, f"{province}.json")

#     print(f"Checking province file: {province_file} exists? {os.path.exists(province_file)}")
#     print(f"Checking economic file: {economic_file} exists? {os.path.exists(economic_file)}")


    
    
#     if not os.path.exists(province_file) or not os.path.exists(economic_file):
#         await update.callback_query.edit_message_text("⛔ فایل‌های موردنیاز پیدا نشد.")
#         return

#     with open(province_file, "r", encoding="utf-8") as f:
#         province_data = json.load(f)

#     with open(economic_file, "r", encoding="utf-8") as f:
#         economic_data = json.load(f)

#     population = province_data.get("population", 0)
#     grain_priority = economic_data.get("grain_priority", [])
#     grains = economic_data.get("grains", {})

#     if not grain_priority:
#         await update.callback_query.edit_message_text("⛔ اولویت غلات تنظیم نشده است.")
#         return

#     if not grains:
#         await update.callback_query.edit_message_text("⛔ درصد مصرف غلات تنظیم نشده است.")
#         return

#     # محاسبه تخمینی کاهش مصرف (مثال فرضی)
#     total_reduction = 0
#     details = []
#     for grain in grain_priority:
#         percentage = grains.get(grain, 100)
#         reduction = 100 - percentage  # درصد کاهش مصرف
#         total_reduction += reduction
#         details.append(f"{grain}: کاهش {reduction}%")

#     avg_reduction = total_reduction / len(grain_priority) if grain_priority else 0
#     estimated_reduction = (population * avg_reduction) / 100  # فرضی برای نمایش

#     msg = (
#         f"👥 جمعیت استان: {population}\n"
#         f"📉 کاهش مصرف میانگین: {avg_reduction:.1f}%\n"
#         f"↘️ تخمین جمعیت کمتر تغذیه‌شده: {int(estimated_reduction)} نفر\n\n"
#         "جزئیات:\n" + "\n".join(details)
#     )

#     keyboard = InlineKeyboardMarkup([
#         [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#     ])

#     await update.callback_query.edit_message_text(msg, reply_markup=keyboard)


COUNTRIES_FILE = "countries.json"
PROVINCES_PATH = "provinces"
ECONOMIC_PATH = "EconomicItems"

BASE_CONSUMPTION_RATES = {
    "گوشت": (300, 1),
    "گندم": (300, 1),
    "ماهی": (250, 1),
    "مرغ": (250, 1),
    "میوه": (200, 1)
}

# async def show_grain_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.callback_query.from_user.id
#     user_data = context.user_data.get(user_id, {})
#     province = user_data.get("selected_province")
   

#     if not province:
#         await update.callback_query.edit_message_text("⛔ ابتدا استان را انتخاب کنید.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ]))
#         return

#     def find_country_by_province(province_name: str) -> str | None:
#         if not os.path.exists(COUNTRIES_FILE):
#             return None
#         with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         countries_areas = data.get("countries_areas", {})
#         for country, provinces in countries_areas.items():
#             if province_name in provinces:
#                 return country
#         return None

#     country = find_country_by_province(province)
#     if not country:
#         await update.callback_query.edit_message_text("⛔ کشور استان پیدا نشد.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ]))
#         return
#     province = province.strip().replace(" ", "_")
#     province_file = os.path.join(PROVINCES_PATH, f"{country}_{province}.json")
#     economic_file = os.path.join(ECONOMIC_PATH, f"{province}.json")

#     if not os.path.exists(province_file) or not os.path.exists(economic_file):
#         await update.callback_query.edit_message_text("⛔ فایل‌های موردنیاز پیدا نشد.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ]))
#         return

#     with open(province_file, "r", encoding="utf-8") as f:
#         province_data = json.load(f)

#     with open(economic_file, "r", encoding="utf-8") as f:
#         economic_data = json.load(f)

#     population = province_data.get("population", 0)
#     grain_priority = economic_data.get("grain_priority", [])
#     grains = economic_data.get("grains", {})

#     if not grain_priority:
#         await update.callback_query.edit_message_text("⛔ اولویت غلات تنظیم نشده است.",
#             parse_mode="Markdown",
#             reply_markup=InlineKeyboardMarkup([
#                 [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#             ]))
#         return

        
#     if not grains:
#         await update.callback_query.edit_message_text("⛔ درصد مصرف غلات تنظیم نشده است.")
#         return

#     # محاسبه میزان مصرف
#     consumption_details = []
#     food_storage = province_data.get("economic_items", {})
#     remaining_population = population

#     for grain in grain_priority:
#         percent = grains.get(grain, 0)
#         base_people, base_units = BASE_CONSUMPTION_RATES.get(grain, (250, 1))

#         multiplier = 1 + (percent / 100)
#         food_amount = food_storage.get(grain, 0)

#         # محاسبه افراد پشتیبانی‌شده
#         # people_supported = int((food_amount * base_people) / multiplier)
#         units_per_person = base_units / base_people  # هر نفر به چند واحد غذا نیاز داره
#         adjusted_units_per_person = units_per_person * multiplier
        
#         people_supported = int(food_amount / adjusted_units_per_person)


#         consumption_details.append(
#             f"{grain} -> {multiplier:.1f} -> {base_people}(نفر)"
#         )

#         if remaining_population > 0:
#             remaining_population -= people_supported


#     # جلوگیری از منفی شدن
#     unfed_population = max(0, remaining_population)

#     # جزئیات درصد مصرف
#     grain_percent_details = [f"{grain}: {grains.get(grain, 0)}%" for grain in grain_priority]

#     msg = (
#         f"👥 جمعیت استان: {population}\n"
#         f"🍽 تخمین جمعیت تغذیه‌نشده: {unfed_population} نفر\n\n"
#         "📦 میزان مصرف:\n" + "\n".join(consumption_details) + "\n\n"
#         "📊 درصد مصرف:\n" + "\n".join(grain_percent_details)
#     )

#     keyboard = InlineKeyboardMarkup([
#         [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
#     ])

#     await update.callback_query.edit_message_text(msg, reply_markup=keyboard)


async def show_grain_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    user_data = context.user_data.get(user_id, {})
    province = user_data.get("selected_province")

    if not province:
        await update.callback_query.edit_message_text(
            "⛔ ابتدا استان را انتخاب کنید.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )
        return

    # پیدا کردن کشور
    def find_country_by_province(province_name: str) -> str | None:
        if not os.path.exists(COUNTRIES_FILE):
            return None
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        countries_areas = data.get("countries_areas", {})
        for country, provinces in countries_areas.items():
            if province_name in provinces:
                return country
        return None

    country = find_country_by_province(province)
    if not country:
        await update.callback_query.edit_message_text(
            "⛔ کشور استان پیدا نشد.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )
        return

    province_clean = province.strip().replace(" ", "_")
    province_file = os.path.join(PROVINCES_PATH, f"{country}_{province_clean}.json")
    economic_file = os.path.join(ECONOMIC_PATH, f"{province_clean}.json")

    if not os.path.exists(province_file) or not os.path.exists(economic_file):
        await update.callback_query.edit_message_text(
            "⛔ فایل‌های موردنیاز پیدا نشد.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )
        return

    with open(province_file, "r", encoding="utf-8") as f:
        province_data = json.load(f)

    with open(economic_file, "r", encoding="utf-8") as f:
        economic_data = json.load(f)

    population = province_data.get("population", 0)
    grain_priority = economic_data.get("grain_priority", [])
    grain_consumption = economic_data.get("grain_consumption", 0)  # درصد کلی مصرف

    if not grain_priority:
        await update.callback_query.edit_message_text(
            "⛔ اولویت غلات تنظیم نشده است.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
            ])
        )
        return

    # محاسبه میزان مصرف
    consumption_details = []
    food_storage = province_data.get("economic_items", {})
    remaining_population = population

    for grain in grain_priority:
        base_people, base_units = BASE_CONSUMPTION_RATES.get(grain, (250, 1))
        multiplier = 1 + (grain_consumption / 100)
        food_amount = food_storage.get(grain, 0)

        units_per_person = base_units / base_people
        adjusted_units_per_person = units_per_person * multiplier
        people_supported = int(food_amount / adjusted_units_per_person)

        consumption_details.append(
            f"🍞 {grain}: {people_supported} نفر ({multiplier:.1f}x)"
        )

        if remaining_population > 0:
            remaining_population -= people_supported

    unfed_population = max(0, remaining_population)

    # جزئیات درصد مصرف برای نمایش
    grain_percent_details = [f"{grain}: {grain_consumption}%" for grain in grain_priority]

    msg = (
        f"👥 جمعیت استان: {population}\n"
        f"🍽 تخمین جمعیت تغذیه‌نشده: {unfed_population} نفر\n\n"
        "📦 میزان مصرف:\n" + "\n".join(consumption_details) + "\n\n"
        "📊 درصد مصرف:\n" + "\n".join(grain_percent_details)
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_food_menu")]
    ])

    await update.callback_query.edit_message_text(msg, reply_markup=keyboard)

def find_country_by_provinces(province_name: str) -> str | None:
    with open("countries.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for country, provinces in data.get("countries_areas", {}).items():
        if province_name in provinces:
            return country
    return None


async def edit_tax_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = context.user_data.get(user_id, {})

    province = user_data.get("selected_province")
    if not province:
        await query.edit_message_text("❗ نام استان در اطلاعات شما یافت نشد.")
        return ConversationHandler.END

    country = find_country_by_provinces(province)
    if not country:
        await query.edit_message_text("❗ کشور مربوط به استان یافت نشد.")
        return ConversationHandler.END

    file_path = f"provinces/{country}_{province.replace(' ', '_')}.json"
    if not os.path.exists(file_path):
        await query.edit_message_text("❗ فایل اطلاعات استان یافت نشد.")
        return ConversationHandler.END

    with open(file_path, encoding="utf-8") as f:
        province_data = json.load(f)

    current_tax = province_data.get("tax", 0)
    if user_id not in context.user_data:
        context.user_data[user_id] = {}

    context.user_data[user_id]["step"] = "editing_province_tax"
    context.user_data[user_id]["flow_type"] = "country_management"
    context.user_data[user_id]["edit_tax_file"] = file_path



    await query.edit_message_text(
        f"✏️ میزان مالیات فعلی در استان {province}: {current_tax}%\n"
        "لطفاً عددی بین 0 تا 100 (مضرب 10) ارسال کن.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ بازگشت", callback_data="back_to_country_menu")]
        ])
    )

    return


# async def handle_tax_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id
#     user_data = context.user_data.get(user_id, {})

#     file_path = user_data.get("edit_tax_file")
#     if not file_path or not os.path.exists(file_path):
#         await update.message.reply_text("❗ فایل استان پیدا نشد.")
#         return True

#     text = update.message.text.strip()
#     try:
#         new_tax = int(text)
#         if new_tax % 10 != 0 or not (0 <= new_tax <= 100):
#             raise ValueError
#     except ValueError:
#         await update.message.reply_text("❌ لطفاً عددی صحیح و مضرب ۱۰ بین ۰ تا ۱۰۰ وارد کن.")
#         return True

#     with open(file_path, "r", encoding="utf-8") as f:
#         data = json.load(f)

#     data["tax"] = new_tax

#     with open(file_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

#     await update.message.reply_text(f"✅ مالیات با موفقیت به {new_tax}% تغییر یافت.")

#     # پاکسازی وضعیت کاربر
#     context.user_data[user_id]["step"] = None
#     context.user_data[user_id]["flow_type"] = None
#     context.user_data[user_id]["edit_tax_file"] = None

#     return True



async def handle_tax_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    logger.info(f"[handle_tax_input] user_id={user_id} sent text: {text}")

    user_data = context.user_data.get(user_id)
    if user_data is None:
        logger.warning(f"[handle_tax_input] No user_data for user {user_id}")
        context.user_data[user_id] = {}
        user_data = context.user_data[user_id]

    file_path = user_data.get("edit_tax_file")
    if not file_path or not os.path.exists(file_path):
        await update.message.reply_text("❗ فایل استان پیدا نشد.")
        logger.error(f"[handle_tax_input] File path not found or does not exist: {file_path}")
        return True

    try:
        new_tax = int(text)
        if new_tax % 10 != 0 or not (0 <= new_tax <= 100):
            raise ValueError("عدد باید مضرب 10 و بین 0 تا 100 باشد.")
    except ValueError as e:
        logger.warning(f"[handle_tax_input] Invalid tax input from user {user_id}: {text}")
        await update.message.reply_text("❌ لطفاً عددی صحیح و مضرب ۱۰ بین ۰ تا ۱۰۰ وارد کن.")
        return True

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["tax"] = new_tax
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[handle_tax_input] Updated tax to {new_tax}% in file {file_path} for user {user_id}")
    except Exception as e:
        logger.error(f"[handle_tax_input] Error updating file {file_path} for user {user_id}: {e}")
        await update.message.reply_text("❗ خطا در ذخیره‌سازی مالیات. لطفاً دوباره تلاش کنید.")
        return True

    await update.message.reply_text(f"✅ مالیات با موفقیت به {new_tax}% تغییر یافت.")

    user_data["step"] = None
    user_data["flow_type"] = None
    user_data["edit_tax_file"] = None
    logger.info(f"[handle_tax_input] Cleared user_data states for user {user_id}")

    return True
