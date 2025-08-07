
# import json
# import os
# import logging
# from datetime import datetime, timedelta

# logger = logging.getLogger(__name__)

# TIMERS_FILE = "timers.json"

# def load_timers():
#     """Load timer states from JSON file"""
#     if not os.path.exists(TIMERS_FILE):
#         # Create default timers file
#         default_timers = {
#             "last_weekly_update": "2025-01-01T00:00:00",
#             "last_tax_calculation": "2025-01-01T00:00:00",
#             "last_economic_tick": "2025-01-01T00:00:00",
#             "last_food_tick": "2025-01-01T00:00:00",
#             "last_cleanup": "2025-01-01T00:00:00"
#         }
#         save_timers(default_timers)
#         logger.info("Created default timers.json file")
#         return default_timers
    
#     try:
#         with open(TIMERS_FILE, 'r', encoding='utf-8') as f:
#             timers = json.load(f)
#             logger.info("Successfully loaded timers from file")
#             return timers
#     except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
#         logger.error(f"Error loading timers: {e}, creating defaults")
#         default_timers = {
#             "last_weekly_update": "2025-01-01T00:00:00",
#             "last_tax_calculation": "2025-01-01T00:00:00", 
#             "last_economic_tick": "2025-01-01T00:00:00",
#             "last_food_tick": "2025-01-01T00:00:00",
#             "last_cleanup": "2025-01-01T00:00:00"
#         }
#         save_timers(default_timers)
#         return default_timers

# def save_timers(timers):
#     """Save timer states to JSON file"""
#     try:
#         with open(TIMERS_FILE, 'w', encoding='utf-8') as f:
#             json.dump(timers, f, ensure_ascii=False, indent=2)
#         logger.info("Successfully saved timers to file")
#         return True
#     except Exception as e:
#         logger.error(f"Error saving timers: {e}")
#         return False

# def should_run_task(task_name, interval_hours=168):  # Default 1 week
#     """Check if a task should run based on last execution time"""
#     try:
#         timers = load_timers()
#         last_run_str = timers.get(task_name)
        
#         if not last_run_str:
#             logger.info(f"No last run time found for {task_name}, should run")
#             return True
            
#         last_run = datetime.fromisoformat(last_run_str)
#         current_time = datetime.now()
#         time_diff = current_time - last_run
        
#         should_run = time_diff >= timedelta(hours=interval_hours)
#         logger.info(f"Task {task_name}: last run {last_run_str}, should run: {should_run}")
#         return should_run
        
#     except Exception as e:
#         logger.error(f"Error checking task {task_name}: {e}")
#         return False

# def update_task_time(task_name):
#     """Update the last execution time for a task"""
#     try:
#         timers = load_timers()
#         timers[task_name] = datetime.now().isoformat()
#         save_timers(timers)
#         logger.info(f"Updated last run time for {task_name}")
#         return True
#     except Exception as e:
#         logger.error(f"Error updating task time for {task_name}: {e}")
#         return False

# def get_time_until_next_run(task_name, interval_hours=168):
#     """Get time remaining until next task run"""
#     try:
#         timers = load_timers()
#         last_run_str = timers.get(task_name)
        
#         if not last_run_str:
#             return timedelta(0)  # Should run now
            
#         last_run = datetime.fromisoformat(last_run_str)
#         next_run = last_run + timedelta(hours=interval_hours)
#         current_time = datetime.now()
        
#         if current_time >= next_run:
#             return timedelta(0)  # Should run now
#         else:
#             return next_run - current_time
            
#     except Exception as e:
#         logger.error(f"Error calculating time until next run for {task_name}: {e}")
#         return timedelta(0)



import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

TIMERS_FILE = "timers.json"

# تمام کلیدهای مورد نیاز با مقادیر پیش‌فرض
DEFAULT_TIMERS = {
    "last_weekly_update": "2025-01-01T00:00:00",
    "last_tax_calculation": "2025-01-01T00:00:00",
    "last_economic_tick": "2025-01-01T00:00:00",
    "last_food_tick": "2025-01-01T00:00:00",
    "last_cleanup": "2025-01-01T00:00:00"
}

def load_timers():
    """Load timer states from JSON file, ensuring all default keys exist."""
    if not os.path.exists(TIMERS_FILE):
        save_timers(DEFAULT_TIMERS.copy())
        logger.info("Created default timers.json file")
        return DEFAULT_TIMERS.copy()

    try:
        with open(TIMERS_FILE, 'r', encoding='utf-8') as f:
            timers = json.load(f)

        # اطمینان از اینکه همه کلیدهای ضروری وجود دارند
        updated = False
        for key, default_value in DEFAULT_TIMERS.items():
            if key not in timers:
                timers[key] = default_value
                updated = True

        if updated:
            save_timers(timers)  # ذخیره مجدد با کلیدهای کامل‌شده

        logger.info("Successfully loaded timers from file")
        return timers

    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        logger.error(f"Error loading timers: {e}, creating default timers.")
        save_timers(DEFAULT_TIMERS.copy())
        return DEFAULT_TIMERS.copy()

def save_timers(timers):
    """Save timer states to JSON file, making sure all required keys exist."""
    try:
        # از حذف اتفاقی کلیدها جلوگیری می‌کنیم
        for key, default_value in DEFAULT_TIMERS.items():
            timers.setdefault(key, default_value)

        with open(TIMERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(timers, f, ensure_ascii=False, indent=2)

        logger.info("Successfully saved timers to file")
        return True
    except Exception as e:
        logger.error(f"Error saving timers: {e}")
        return False

def should_run_task(task_name, interval_hours=168):
    """Check if a task should run based on last execution time"""
    try:
        timers = load_timers()
        last_run_str = timers.get(task_name)

        if not last_run_str:
            logger.info(f"No last run time found for {task_name}, should run")
            return True

        last_run = datetime.fromisoformat(last_run_str)
        current_time = datetime.now()
        time_diff = current_time - last_run

        should_run = time_diff >= timedelta(hours=interval_hours)
        logger.info(f"Task {task_name}: last run {last_run_str}, should run: {should_run}")
        return should_run

    except Exception as e:
        logger.error(f"Error checking task {task_name}: {e}")
        return False

def update_task_time(task_name):
    """Update the last execution time for a task"""
    try:
        timers = load_timers()
        timers[task_name] = datetime.now().isoformat()
        save_timers(timers)
        logger.info(f"Updated last run time for {task_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating task time for {task_name}: {e}")
        return False

def get_time_until_next_run(task_name, interval_hours=168):
    """Get time remaining until next task run"""
    try:
        timers = load_timers()
        last_run_str = timers.get(task_name)

        if not last_run_str:
            return timedelta(0)  # Should run now

        last_run = datetime.fromisoformat(last_run_str)
        next_run = last_run + timedelta(hours=interval_hours)
        current_time = datetime.now()

        if current_time >= next_run:
            return timedelta(0)
        else:
            return next_run - current_time

    except Exception as e:
        logger.error(f"Error calculating time until next run for {task_name}: {e}")
        return timedelta(0)
