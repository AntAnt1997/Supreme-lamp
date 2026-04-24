"""Notification service – SMS (Twilio), email (SendGrid), and in-app notifications."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def send_notification(
    db,
    patient_id: int,
    notification_type,
    channel,
    content: str,
    subject: Optional[str] = None,
) -> None:
    """
    Create a Notification record and attempt delivery via the specified channel.
    """
    from healthcare.models.notification import Notification

    notif = Notification(
        patient_id=patient_id,
        channel=channel,
        notification_type=notification_type,
        subject=subject,
        content=content,
        is_sent=False,
    )
    db.add(notif)
    db.flush()

    try:
        _deliver(notif, db)
    except Exception as e:
        logger.error("Notification delivery failed (id=%s): %s", notif.id, e)
        notif.error_message = str(e)
        db.add(notif)


def _deliver(notif, db) -> None:
    from healthcare.models.notification import NotificationChannel
    from healthcare.models.patient import Patient

    patient = db.query(Patient).filter(Patient.id == notif.patient_id).first()
    if not patient:
        return

    if notif.channel == NotificationChannel.sms:
        _send_sms(notif, patient)
    elif notif.channel == NotificationChannel.email:
        _send_email(notif, patient)
    elif notif.channel == NotificationChannel.in_app:
        # In-app notifications are read directly from the DB
        pass

    notif.is_sent = True
    notif.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(notif)


def _send_sms(notif, patient) -> None:
    from healthcare.config import healthcare_settings

    phone = patient.phone
    if not phone:
        logger.debug("Patient %d has no phone – skipping SMS", patient.id)
        return

    sid = healthcare_settings.twilio_account_sid
    token = healthcare_settings.twilio_auth_token
    from_number = healthcare_settings.twilio_from_number

    if not sid or sid == "your_twilio_account_sid":
        logger.debug("Twilio not configured – SMS skipped (demo mode)")
        return

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body=notif.content,
            from_=from_number,
            to=phone,
        )
        notif.external_id = msg.sid
    except Exception as e:
        raise RuntimeError(f"Twilio SMS error: {e}")


def _send_email(notif, patient) -> None:
    from healthcare.config import healthcare_settings

    api_key = healthcare_settings.sendgrid_api_key
    if not api_key or api_key == "your_sendgrid_api_key":
        logger.debug("SendGrid not configured – email skipped (demo mode)")
        return

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=(healthcare_settings.from_email, healthcare_settings.from_name),
            to_emails=patient.email,
            subject=notif.subject or "Healthcare Platform Notification",
            plain_text_content=notif.content,
        )
        response = sg.send(message)
        notif.external_id = response.headers.get("X-Message-Id", "")
    except Exception as e:
        raise RuntimeError(f"SendGrid email error: {e}")
