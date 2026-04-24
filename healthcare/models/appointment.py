"""Appointment model – scheduling across all departments."""

import enum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class AppointmentType(str, enum.Enum):
    in_person = "in_person"
    telehealth = "telehealth"


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    checked_in = "checked_in"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    waitlisted = "waitlisted"


class RecurrencePattern(str, enum.Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Timing
    scheduled_start = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Type & status
    appointment_type = Column(Enum(AppointmentType), default=AppointmentType.in_person)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled, index=True)

    # Reason & notes
    reason = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    diagnosis_codes = Column(JSON, default=list)      # ["ICD-10 codes"]
    procedure_codes = Column(JSON, default=list)      # ["CPT codes"]

    # Recurrence
    recurrence = Column(Enum(RecurrencePattern), default=RecurrencePattern.none)
    recurrence_end_date = Column(DateTime, nullable=True)
    parent_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    # Telehealth
    telehealth_link = Column(String(500), nullable=True)
    telehealth_passcode = Column(String(50), nullable=True)

    # Waitlist
    is_waitlisted = Column(Boolean, default=False)
    waitlist_position = Column(Integer, nullable=True)

    # Reminders sent flags
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_1h_sent = Column(Boolean, default=False)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")
    department = relationship("Department", foreign_keys=[department_id])
    bill = relationship("Bill", back_populates="appointment", uselist=False)

    def __repr__(self):
        return (
            f"<Appointment #{self.id} patient={self.patient_id} "
            f"provider={self.provider_id} at={self.scheduled_start}>"
        )
