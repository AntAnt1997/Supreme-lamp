"""24/7 AI workflow orchestration – Celery Beat periodic tasks for proactive AI actions."""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def run_post_visit_followup(appointment_id: int):
    """
    Send a post-visit AI follow-up survey and check-in message to the patient.
    Called by Celery 24 hours after appointment completion.
    """
    from healthcare.database.db import get_session
    from healthcare.models.appointment import Appointment, AppointmentStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel

    with get_session() as db:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt or appt.status != AppointmentStatus.completed:
            return

        message = (
            f"Hi! We hope your visit on {appt.scheduled_start.strftime('%B %d')} went well. "
            "How are you feeling? Our AI assistant is available 24/7 at your patient portal "
            "if you have any questions or concerns. You can also schedule a follow-up appointment there."
        )
        send_notification(
            db=db,
            patient_id=appt.patient_id,
            notification_type=NotificationType.follow_up,
            channel=NotificationChannel.email,
            content=message,
            subject="How are you feeling after your visit?",
        )
        logger.info("Post-visit follow-up sent for appointment %d", appointment_id)


def run_medication_reminder_check():
    """
    Scan active patients who have current medications and send daily reminders
    (if they opted in). Called by Celery Beat daily.
    """
    from healthcare.database.db import get_session
    from healthcare.models.patient import Patient, PatientStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel

    with get_session() as db:
        patients = (
            db.query(Patient)
            .filter(
                Patient.status == PatientStatus.active,
                Patient.current_medications != None,
            )
            .all()
        )
        count = 0
        for patient in patients:
            if not patient.current_medications:
                continue
            med_list = ", ".join(
                m.get("name", str(m)) for m in patient.current_medications
            )
            message = (
                f"Daily medication reminder: {med_list}. "
                "Please take your medications as prescribed. Contact your provider if you have concerns."
            )
            send_notification(
                db=db,
                patient_id=patient.id,
                notification_type=NotificationType.medication_reminder,
                channel=NotificationChannel.sms,
                content=message,
            )
            count += 1
        logger.info("Sent medication reminders to %d patients", count)


def run_overdue_bill_check():
    """
    Find overdue bills and send reminder notifications.
    Called by Celery Beat daily.
    """
    from healthcare.database.db import get_session
    from healthcare.models.billing import Bill, BillStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel

    with get_session() as db:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        overdue_bills = (
            db.query(Bill)
            .filter(
                Bill.due_date < now,
                Bill.balance_due > 0,
                Bill.status.not_in([BillStatus.paid, BillStatus.voided]),
            )
            .all()
        )
        for bill in overdue_bills:
            if bill.status != BillStatus.overdue:
                bill.status = BillStatus.overdue
                db.add(bill)

            send_notification(
                db=db,
                patient_id=bill.patient_id,
                notification_type=NotificationType.bill_overdue,
                channel=NotificationChannel.email,
                content=(
                    f"Your bill #{bill.id} of ${bill.balance_due:.2f} is overdue. "
                    "Please log in to your patient portal to make a payment or set up a payment plan."
                ),
                subject=f"Payment Overdue – Bill #{bill.id}",
            )
        logger.info("Processed %d overdue bills", len(overdue_bills))


def run_appointment_slot_check():
    """
    Check waitlisted appointments and notify patients when a slot opens.
    Called by Celery Beat every 15 minutes.
    """
    from healthcare.database.db import get_session
    from healthcare.models.appointment import Appointment, AppointmentStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel

    with get_session() as db:
        # Find cancelled slots that have waitlisted patients
        cancelled = (
            db.query(Appointment)
            .filter(Appointment.status == AppointmentStatus.cancelled)
            .all()
        )
        for cancelled_appt in cancelled:
            waitlisted = (
                db.query(Appointment)
                .filter(
                    Appointment.provider_id == cancelled_appt.provider_id,
                    Appointment.scheduled_start == cancelled_appt.scheduled_start,
                    Appointment.status == AppointmentStatus.waitlisted,
                )
                .order_by(Appointment.created_at)
                .first()
            )
            if waitlisted:
                waitlisted.status = AppointmentStatus.scheduled
                waitlisted.is_waitlisted = False
                db.add(waitlisted)
                send_notification(
                    db=db,
                    patient_id=waitlisted.patient_id,
                    notification_type=NotificationType.appointment_confirmed,
                    channel=NotificationChannel.email,
                    content=(
                        f"Great news! A slot has opened up for your waitlisted appointment "
                        f"on {cancelled_appt.scheduled_start.strftime('%B %d at %I:%M %p')}. "
                        "Your appointment has been confirmed."
                    ),
                    subject="Appointment Slot Available – Confirmed!",
                )
        logger.info("Processed waitlist slots for %d cancelled appointments", len(cancelled))
