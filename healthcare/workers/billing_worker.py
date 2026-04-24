"""Celery tasks for billing-related background jobs."""

import logging

from healthcare.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="healthcare.workers.billing_worker.notify_bill_issued", bind=True, max_retries=3)
def notify_bill_issued(self, bill_id: int):
    """Notify patient that a new bill has been issued."""
    try:
        from healthcare.database.db import get_session
        from healthcare.models.billing import Bill
        from healthcare.services.notifications import send_notification
        from healthcare.models.notification import NotificationType, NotificationChannel

        with get_session() as db:
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            if not bill:
                return
            send_notification(
                db=db,
                patient_id=bill.patient_id,
                notification_type=NotificationType.bill_issued,
                channel=NotificationChannel.email,
                content=(
                    f"A new bill has been issued on your account. "
                    f"Bill #{bill.id}: ${bill.total:.2f} due. "
                    "Please log in to your patient portal to view and pay."
                ),
                subject=f"New Medical Bill – ${bill.total:.2f}",
            )
    except Exception as exc:
        logger.error("notify_bill_issued failed for bill %d: %s", bill_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="healthcare.workers.billing_worker.check_overdue_bills")
def check_overdue_bills():
    """Daily task: find overdue bills and send reminders."""
    from healthcare.ai.workflows import run_overdue_bill_check
    run_overdue_bill_check()


@celery_app.task(name="healthcare.workers.billing_worker.send_billing_reminders")
def send_billing_reminders():
    """Send reminders for unpaid bills that are not yet overdue."""
    from healthcare.database.db import get_session
    from healthcare.models.billing import Bill, BillStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel
    from datetime import datetime, timezone

    with get_session() as db:
        unpaid = (
            db.query(Bill)
            .filter(
                Bill.balance_due > 0,
                Bill.status.in_([BillStatus.issued, BillStatus.partially_paid]),
            )
            .all()
        )
        for bill in unpaid:
            send_notification(
                db=db,
                patient_id=bill.patient_id,
                notification_type=NotificationType.bill_issued,
                channel=NotificationChannel.email,
                content=(
                    f"Friendly reminder: Bill #{bill.id} has a balance of ${bill.balance_due:.2f}. "
                    "Log in to your patient portal to pay or set up a payment plan."
                ),
                subject=f"Payment Reminder – Bill #{bill.id}",
            )
            bill.reminder_sent_count = (bill.reminder_sent_count or 0) + 1
            bill.last_reminder_sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.add(bill)
        logger.info("Sent billing reminders for %d bills", len(unpaid))
