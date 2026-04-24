"""Appointment & medication reminder helpers."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def send_appointment_reminder_now(appointment_id: int, reminder_type: str):
    """
    Send appointment reminder immediately.
    reminder_type: "24h" or "1h"
    """
    from healthcare.database.db import get_session
    from healthcare.models.appointment import Appointment, AppointmentStatus
    from healthcare.services.notifications import send_notification
    from healthcare.models.notification import NotificationType, NotificationChannel

    with get_session() as db:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            logger.warning("Appointment %d not found for reminder", appointment_id)
            return
        if appt.status in (AppointmentStatus.cancelled, AppointmentStatus.no_show):
            return

        if reminder_type == "24h" and appt.reminder_24h_sent:
            return
        if reminder_type == "1h" and appt.reminder_1h_sent:
            return

        time_str = appt.scheduled_start.strftime("%B %d at %I:%M %p")
        content = (
            f"Reminder: You have an appointment {reminder_type} from now "
            f"on {time_str}. "
        )
        if appt.telehealth_link:
            content += f"Telehealth link: {appt.telehealth_link}"
        else:
            content += "Please arrive 10 minutes early."

        notif_type = (
            NotificationType.appointment_reminder_24h
            if reminder_type == "24h"
            else NotificationType.appointment_reminder_1h
        )

        send_notification(
            db=db,
            patient_id=appt.patient_id,
            notification_type=notif_type,
            channel=NotificationChannel.sms,
            content=content,
        )
        send_notification(
            db=db,
            patient_id=appt.patient_id,
            notification_type=notif_type,
            channel=NotificationChannel.email,
            content=content,
            subject=f"Appointment Reminder – {time_str}",
        )

        if reminder_type == "24h":
            appt.reminder_24h_sent = True
        else:
            appt.reminder_1h_sent = True
        db.add(appt)
        logger.info("Sent %s reminder for appointment %d", reminder_type, appointment_id)
