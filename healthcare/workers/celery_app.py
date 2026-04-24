"""Celery application configuration for 24/7 healthcare background workflows."""

import os
from celery import Celery
from celery.schedules import crontab

from healthcare.config import healthcare_settings

celery_app = Celery(
    "healthcare",
    broker=healthcare_settings.celery_broker_url,
    backend=healthcare_settings.celery_result_backend,
    include=[
        "healthcare.workers.appointment_worker",
        "healthcare.workers.billing_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# ── Celery Beat Schedule (24/7 Periodic Tasks) ─────────────────────────────────
celery_app.conf.beat_schedule = {
    # Check overdue bills every day at 8 AM UTC
    "check-overdue-bills-daily": {
        "task": "healthcare.workers.billing_worker.check_overdue_bills",
        "schedule": crontab(hour=8, minute=0),
    },
    # Send medication reminders every day at 8 AM UTC
    "medication-reminders-daily": {
        "task": "healthcare.workers.appointment_worker.medication_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    # Check waitlist / slot availability every 15 minutes
    "check-waitlist-slots": {
        "task": "healthcare.workers.appointment_worker.check_waitlist_slots",
        "schedule": crontab(minute="*/15"),
    },
    # Send billing reminders for unpaid bills every 3 days at 9 AM
    "billing-reminders": {
        "task": "healthcare.workers.billing_worker.send_billing_reminders",
        "schedule": crontab(hour=9, minute=0, day_of_week="1,4"),  # Mon & Thu
    },
}
