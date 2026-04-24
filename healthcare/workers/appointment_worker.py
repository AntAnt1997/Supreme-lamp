"""Celery tasks for appointment-related background jobs."""

import logging

from healthcare.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="healthcare.workers.appointment_worker.send_appointment_reminder",
                 bind=True, max_retries=3, default_retry_delay=300)
def send_appointment_reminder(self, appointment_id: int, reminder_type: str):
    """Send appointment reminder (24h or 1h before the appointment)."""
    try:
        from healthcare.ai.reminders import send_appointment_reminder_now
        send_appointment_reminder_now(appointment_id, reminder_type)
    except Exception as exc:
        logger.error("Reminder task failed for appointment %d: %s", appointment_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="healthcare.workers.appointment_worker.send_post_visit_followup",
                 bind=True, max_retries=2)
def send_post_visit_followup(self, appointment_id: int):
    """Send post-visit follow-up message to a patient."""
    try:
        from healthcare.ai.workflows import run_post_visit_followup
        run_post_visit_followup(appointment_id)
    except Exception as exc:
        logger.error("Post-visit follow-up failed for appointment %d: %s", appointment_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="healthcare.workers.appointment_worker.medication_reminders")
def medication_reminders():
    """Daily task: send medication reminders to active patients."""
    from healthcare.ai.workflows import run_medication_reminder_check
    run_medication_reminder_check()


@celery_app.task(name="healthcare.workers.appointment_worker.check_waitlist_slots")
def check_waitlist_slots():
    """Every 15 minutes: check for cancelled slots and promote waitlisted patients."""
    from healthcare.ai.workflows import run_appointment_slot_check
    run_appointment_slot_check()
