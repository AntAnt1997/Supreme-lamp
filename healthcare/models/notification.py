"""Notification model – records of all SMS/email/push notifications sent."""

import enum

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class NotificationChannel(str, enum.Enum):
    email = "email"
    sms = "sms"
    push = "push"
    in_app = "in_app"


class NotificationType(str, enum.Enum):
    appointment_reminder_24h = "appointment_reminder_24h"
    appointment_reminder_1h = "appointment_reminder_1h"
    appointment_confirmed = "appointment_confirmed"
    appointment_cancelled = "appointment_cancelled"
    bill_issued = "bill_issued"
    bill_overdue = "bill_overdue"
    payment_received = "payment_received"
    lab_results_ready = "lab_results_ready"
    prescription_ready = "prescription_ready"
    follow_up = "follow_up"
    medication_reminder = "medication_reminder"
    general = "general"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    channel = Column(Enum(NotificationChannel), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)

    subject = Column(String(255), nullable=True)   # Used for email
    content = Column(Text, nullable=False)

    # External delivery IDs
    external_id = Column(String(255), nullable=True)    # Twilio/SendGrid message ID

    sent_at = Column(DateTime, nullable=True)
    is_sent = Column(Boolean, default=False, index=True)
    error_message = Column(Text, nullable=True)

    # Read tracking (for in-app)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="notifications")

    def __repr__(self):
        return f"<Notification #{self.id} {self.notification_type} -> patient={self.patient_id}>"
