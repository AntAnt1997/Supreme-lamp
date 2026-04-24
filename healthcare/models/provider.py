"""Provider model – doctors, dentists, and all healthcare professionals."""

import enum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Enum, ForeignKey, JSON, Float,
)
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class StaffRole(str, enum.Enum):
    physician = "physician"
    dentist = "dentist"
    nurse_practitioner = "nurse_practitioner"
    physician_assistant = "physician_assistant"
    registered_nurse = "registered_nurse"
    licensed_practical_nurse = "licensed_practical_nurse"
    medical_assistant = "medical_assistant"
    therapist = "therapist"
    pharmacist = "pharmacist"
    radiologist = "radiologist"
    pathologist = "pathologist"
    technician = "technician"
    social_worker = "social_worker"
    dietitian = "dietitian"
    admin = "admin"           # administrative staff / superuser


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Auth (staff can log in to the portal)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    mfa_secret = Column(String(64), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    role = Column(Enum(StaffRole), nullable=False, default=StaffRole.physician)

    # Personal
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    phone = Column(String(30), nullable=True)
    photo_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

    # Credentials
    npi_number = Column(String(20), nullable=True, unique=True)   # National Provider Identifier
    license_number = Column(String(80), nullable=True)
    license_state = Column(String(50), nullable=True)
    board_certifications = Column(JSON, default=list)  # ["Cardiology Board Certified", ...]
    education = Column(JSON, default=list)             # [{"school": "...", "degree": "..."}]
    languages = Column(JSON, default=list)             # ["English", "Spanish"]

    # Department link (primary)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)

    # Additional specialties (stored as JSON list of specialty IDs)
    specialty_ids = Column(JSON, default=list)

    # Accepted insurance plans (JSON list of strings)
    accepted_insurance = Column(JSON, default=list)

    # Schedule template (JSON: {day_of_week: [{start: "09:00", end: "17:00"}]})
    schedule_template = Column(JSON, default=dict)

    # Appointment settings
    slot_duration_minutes = Column(Integer, default=30)
    telehealth_available = Column(Boolean, default=True)
    in_person_available = Column(Boolean, default=True)

    # Rating / stats (updated by background jobs)
    average_rating = Column(Float, default=0.0)
    total_appointments = Column(Integer, default=0)

    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    department = relationship("Department", foreign_keys=[department_id])
    appointments = relationship("Appointment", back_populates="provider", lazy="dynamic")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def display_title(self) -> str:
        prefix = "Dr." if self.role in (StaffRole.physician, StaffRole.dentist) else ""
        return f"{prefix} {self.full_name}".strip()

    def __repr__(self):
        return f"<Provider {self.display_title} ({self.role.value})>"
