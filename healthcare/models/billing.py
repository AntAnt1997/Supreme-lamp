"""Billing models – bills, payments, insurance claims."""

import enum

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, Enum, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from healthcare.models.base import Base, TimestampMixin


class BillStatus(str, enum.Enum):
    draft = "draft"
    issued = "issued"
    partially_paid = "partially_paid"
    paid = "paid"
    overdue = "overdue"
    in_collections = "in_collections"
    voided = "voided"
    disputed = "disputed"


class PaymentMethod(str, enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    hsa = "hsa"
    fsa = "fsa"
    bank_transfer = "bank_transfer"
    insurance = "insurance"
    cash = "cash"
    payment_plan = "payment_plan"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"
    disputed = "disputed"


class ClaimStatus(str, enum.Enum):
    not_submitted = "not_submitted"
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    partially_approved = "partially_approved"
    denied = "denied"
    appealed = "appealed"


class Bill(Base, TimestampMixin):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)

    # Line items stored as JSON: [{"description": "...", "code": "CPT...", "amount": 0.0}]
    line_items = Column(JSON, default=list)

    # Amounts
    subtotal = Column(Float, nullable=False, default=0.0)
    insurance_adjustment = Column(Float, default=0.0)   # Amount covered by insurance
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    amount_paid = Column(Float, default=0.0)
    balance_due = Column(Float, nullable=False, default=0.0)

    # Insurance claim
    claim_status = Column(Enum(ClaimStatus), default=ClaimStatus.not_submitted)
    claim_id = Column(String(80), nullable=True)          # External claim reference
    insurance_eob = Column(Text, nullable=True)           # Explanation of Benefits (JSON/text)

    # Status & dates
    status = Column(Enum(BillStatus), default=BillStatus.draft, index=True)
    due_date = Column(DateTime, nullable=True)
    statement_date = Column(DateTime, nullable=True)

    # Payment plan
    is_payment_plan = Column(Boolean, default=False)
    payment_plan_months = Column(Integer, nullable=True)
    payment_plan_monthly_amount = Column(Float, nullable=True)

    # Reminders
    reminder_sent_count = Column(Integer, default=0)
    last_reminder_sent_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="bills")
    appointment = relationship("Appointment", back_populates="bill")
    payments = relationship("Payment", back_populates="bill", lazy="dynamic")

    def __repr__(self):
        return f"<Bill #{self.id} patient={self.patient_id} total={self.total:.2f} status={self.status}>"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    amount = Column(Float, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, index=True)

    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True)
    stripe_charge_id = Column(String(255), nullable=True)

    # Receipt
    receipt_url = Column(String(500), nullable=True)
    receipt_pdf_path = Column(String(500), nullable=True)

    processed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    bill = relationship("Bill", back_populates="payments")

    def __repr__(self):
        return f"<Payment #{self.id} amount={self.amount:.2f} status={self.status}>"
