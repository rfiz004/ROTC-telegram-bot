from apscheduler.schedulers.asyncio import AsyncIOScheduler
import subprocess
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

def schedule_auto_push():
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)

    @scheduler.scheduled_job("interval", minutes=15)
    def auto_push():
        logger.info(f"🕒 Running auto push at {datetime.now().isoformat()}")
        try:
            subprocess.run(["python3", "run_git_push.py"], check=True)
            logger.info("✅ Git auto push succeeded.")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git auto push failed: {e}")

    scheduler.start()
