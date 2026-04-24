"""Patient model – demographics, insurance, medical history."""

import enum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, Enum, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class PatientStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deceased = "deceased"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    non_binary = "non_binary"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Auth
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    mfa_secret = Column(String(64), nullable=True)   # TOTP secret
    mfa_enabled = Column(Boolean, default=False)

    # Demographics
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=True)
    phone = Column(String(30), nullable=True)
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(80), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(60), default="US")

    # Emergency Contact
    emergency_contact_name = Column(String(160), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    emergency_contact_relationship = Column(String(60), nullable=True)

    # Insurance
    insurance_provider = Column(String(120), nullable=True)
    insurance_member_id = Column(String(80), nullable=True)
    insurance_group_number = Column(String(80), nullable=True)
    insurance_plan_name = Column(String(120), nullable=True)
    insurance_card_front_url = Column(String(500), nullable=True)
    insurance_card_back_url = Column(String(500), nullable=True)

    # Medical history (stored as JSON arrays of strings for simplicity)
    allergies = Column(JSON, default=list)           # ["Penicillin", "Sulfa"]
    current_medications = Column(JSON, default=list) # [{"name": "...", "dose": "..."}]
    past_medical_history = Column(JSON, default=list)
    past_surgical_history = Column(JSON, default=list)
    family_history = Column(JSON, default=list)
    immunizations = Column(JSON, default=list)

    # Status
    status = Column(Enum(PatientStatus), default=PatientStatus.active, nullable=False)
    preferred_language = Column(String(40), default="English")
    notes = Column(Text, nullable=True)

    # Relationships
    appointments = relationship("Appointment", back_populates="patient", lazy="dynamic")
    bills = relationship("Bill", back_populates="patient", lazy="dynamic")
    ai_conversations = relationship("AIConversation", back_populates="patient", lazy="dynamic")
    notifications = relationship("Notification", back_populates="patient", lazy="dynamic")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Patient {self.full_name} ({self.email})>"
