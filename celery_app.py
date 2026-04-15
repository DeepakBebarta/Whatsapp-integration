"""
src/tasks/celery_app.py
Celery application for Axension AI Agent 1 scheduled tasks.

Start worker:  celery -A src.tasks.celery_app worker --loglevel=info
Start beat:    celery -A src.tasks.celery_app beat --loglevel=info
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# ── Celery app ────────────────────────────────────────────────────────────────
app = Celery(
    "axension_ai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

# ── Beat schedule ─────────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Dev heartbeat — fires every 5 minutes
    "heartbeat-every-5-min": {
        "task": "src.tasks.celery_app.send_heartbeat",
        "schedule": 300,  # seconds
    },
    # Daily supplier follow-up — 8:00 AM IST = 02:30 UTC
    "daily-supplier-followup": {
        "task": "src.tasks.celery_app.daily_supplier_followup",
        "schedule": crontab(hour=2, minute=30),
    },
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ── Tasks ─────────────────────────────────────────────────────────────────────
@app.task(name="src.tasks.celery_app.send_heartbeat")
def send_heartbeat():
    """
    Dev task: sends a WhatsApp heartbeat message every 5 minutes.
    Confirms the Celery + WhatsApp pipeline is alive.
    """
    # Import here to avoid circular issues at module load
    from src.whatsapp.client import send_text

    IST = timezone(timedelta(hours=5, minutes=30))
    ts = datetime.now(IST).strftime("%d %b %Y %H:%M IST")
    test_number = os.getenv("HEARTBEAT_NUMBER", "918121444200")

    message = f"✅ Axension AI is running — {ts}"
    logger.info(f"[Heartbeat] Sending to {test_number}: {message}")

    result = send_text(test_number, message)
    logger.info(f"[Heartbeat] API response: {result}")
    return result


@app.task(name="src.tasks.celery_app.daily_supplier_followup")
def daily_supplier_followup():
    """
    Placeholder for Agent 1 daily supplier follow-up logic.
    Will be replaced with real PO fetch + message dispatch in Day 2.
    """
    IST = timezone(timedelta(hours=5, minutes=30))
    ts = datetime.now(IST).strftime("%d %b %Y %H:%M IST")

    logger.info(f"[Agent 1] daily_supplier_followup placeholder — {ts}")
    # TODO Day 2: fetch overdue POs from DB, run template logic, send messages
    return {"status": "placeholder", "timestamp": ts}
