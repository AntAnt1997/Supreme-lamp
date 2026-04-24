"""AI Conversation model – stores all 24/7 chat sessions and triage results."""

import enum

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class UrgencyLevel(str, enum.Enum):
    emergency = "emergency"     # Call 911 / go to ER immediately
    urgent = "urgent"           # Urgent care within hours
    routine = "routine"         # Schedule appointment within days/weeks
    self_care = "self_care"     # Manage at home


class AIConversation(Base, TimestampMixin):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    session_token = Column(String(128), nullable=False, unique=True, index=True)

    # Full message history as JSON list:
    # [{"role": "user"|"assistant", "content": "...", "timestamp": "..."}]
    messages = Column(JSON, default=list)

    # Triage output
    triage_completed = Column(Boolean, default=False)
    urgency_level = Column(Enum(UrgencyLevel), nullable=True, index=True)
    suggested_department = Column(String(120), nullable=True)
    triage_summary = Column(Text, nullable=True)
    triage_confidence = Column(Float, nullable=True)

    # Appointment recommendation
    recommended_provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)

    # Linked appointment (if patient booked from chat)
    booked_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)

    # Meta
    channel = Column(String(30), default="web")   # "web", "mobile", "sms"
    is_anonymous = Column(Boolean, default=False)
    ended_at = Column(String(30), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="ai_conversations")

    def __repr__(self):
        return f"<AIConversation #{self.id} patient={self.patient_id} urgency={self.urgency_level}>"
