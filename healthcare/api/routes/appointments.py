"""Appointment booking, rescheduling, and cancellation API routes."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from healthcare.api.auth_utils import get_current_user, require_staff
from healthcare.database.db import get_db
from healthcare.models.appointment import (
    Appointment, AppointmentType, AppointmentStatus, RecurrencePattern,
)
from healthcare.models.patient import Patient
from healthcare.models.provider import Provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/appointments", tags=["appointments"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    provider_id: int
    department_id: Optional[int] = None
    scheduled_start: datetime
    appointment_type: AppointmentType = AppointmentType.in_person
    reason: Optional[str] = None
    chief_complaint: Optional[str] = None
    recurrence: RecurrencePattern = RecurrencePattern.none
    recurrence_end_date: Optional[datetime] = None


class AppointmentUpdate(BaseModel):
    scheduled_start: Optional[datetime] = None
    appointment_type: Optional[AppointmentType] = None
    reason: Optional[str] = None
    chief_complaint: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    clinical_notes: Optional[str] = None
    diagnosis_codes: Optional[List[str]] = None
    procedure_codes: Optional[List[str]] = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    provider_id: int
    department_id: Optional[int]
    scheduled_start: datetime
    scheduled_end: datetime
    appointment_type: str
    status: str
    reason: Optional[str]
    chief_complaint: Optional[str]
    telehealth_link: Optional[str]
    recurrence: str
    is_waitlisted: bool

    class Config:
        from_attributes = True


# ── Helpers ────────────────────────────────────────────────────────────────────

def _assert_no_conflict(db: Session, provider_id: int, start: datetime, end: datetime, exclude_id: int = None):
    query = db.query(Appointment).filter(
        Appointment.provider_id == provider_id,
        Appointment.status.not_in([AppointmentStatus.cancelled, AppointmentStatus.no_show]),
        Appointment.scheduled_start < end,
        Appointment.scheduled_end > start,
    )
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)
    if query.first():
        raise HTTPException(409, "Time slot is already booked for this provider")


def _build_appointment(
    db: Session,
    patient_id: int,
    body: AppointmentCreate,
) -> Appointment:
    provider = db.query(Provider).filter(Provider.id == body.provider_id).first()
    if not provider or not provider.is_active:
        raise HTTPException(404, "Provider not found")

    start = body.scheduled_start.replace(tzinfo=None)
    end = start + timedelta(minutes=provider.slot_duration_minutes)

    _assert_no_conflict(db, body.provider_id, start, end)

    telehealth_link = None
    if body.appointment_type == AppointmentType.telehealth:
        # Generate a simple meeting token (in production use Twilio Video / Zoom API)
        telehealth_link = f"https://meet.healthcare.local/{secrets.token_urlsafe(12)}"

    return Appointment(
        patient_id=patient_id,
        provider_id=body.provider_id,
        department_id=body.department_id or provider.department_id,
        scheduled_start=start,
        scheduled_end=end,
        appointment_type=body.appointment_type,
        status=AppointmentStatus.scheduled,
        reason=body.reason,
        chief_complaint=body.chief_complaint,
        telehealth_link=telehealth_link,
        recurrence=body.recurrence,
        recurrence_end_date=body.recurrence_end_date,
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/", response_model=AppointmentOut, status_code=201)
def book_appointment(
    body: AppointmentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Patient):
        patient_id = current_user.id
    else:
        raise HTTPException(403, "Use /api/appointments/staff/book to book on behalf of a patient")

    appt = _build_appointment(db, patient_id, body)
    db.add(appt)
    db.flush()

    # Enqueue notification
    _schedule_notifications(appt)

    # Create recurring chain if needed
    if body.recurrence != RecurrencePattern.none and body.recurrence_end_date:
        _create_recurrences(db, appt, body)

    return appt


@router.post("/staff/book", response_model=AppointmentOut, status_code=201)
def staff_book_appointment(
    patient_id: int,
    body: AppointmentCreate,
    _=Depends(require_staff),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(404, "Patient not found")
    appt = _build_appointment(db, patient_id, body)
    db.add(appt)
    db.flush()
    _schedule_notifications(appt)
    return appt


@router.get("/", response_model=List[AppointmentOut])
def list_appointments(
    status_filter: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Patient):
        query = db.query(Appointment).filter(Appointment.patient_id == current_user.id)
    else:
        query = db.query(Appointment).filter(Appointment.provider_id == current_user.id)

    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    return query.order_by(Appointment.scheduled_start.desc()).limit(100).all()


@router.get("/{appt_id}", response_model=AppointmentOut)
def get_appointment(
    appt_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    _assert_access(current_user, appt)
    return appt


@router.patch("/{appt_id}", response_model=AppointmentOut)
def update_appointment(
    appt_id: int,
    body: AppointmentUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    _assert_access(current_user, appt)

    if body.scheduled_start:
        provider = db.query(Provider).filter(Provider.id == appt.provider_id).first()
        start = body.scheduled_start.replace(tzinfo=None)
        end = start + timedelta(minutes=provider.slot_duration_minutes)
        _assert_no_conflict(db, appt.provider_id, start, end, exclude_id=appt_id)
        appt.scheduled_start = start
        appt.scheduled_end = end

    for field in ("appointment_type", "reason", "chief_complaint", "status",
                  "clinical_notes", "diagnosis_codes", "procedure_codes"):
        val = getattr(body, field)
        if val is not None:
            setattr(appt, field, val)

    db.add(appt)
    return appt


@router.delete("/{appt_id}", status_code=204)
def cancel_appointment(
    appt_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    _assert_access(current_user, appt)
    appt.status = AppointmentStatus.cancelled
    db.add(appt)


@router.post("/{appt_id}/waitlist")
def join_waitlist(
    appt_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(404, "Appointment not found")
    # Create a waitlisted copy for the current patient
    if not isinstance(current_user, Patient):
        raise HTTPException(403, "Patients only")

    new_appt = Appointment(
        patient_id=current_user.id,
        provider_id=appt.provider_id,
        department_id=appt.department_id,
        scheduled_start=appt.scheduled_start,
        scheduled_end=appt.scheduled_end,
        appointment_type=appt.appointment_type,
        status=AppointmentStatus.waitlisted,
        reason=appt.reason,
        is_waitlisted=True,
    )
    db.add(new_appt)
    db.flush()
    return {"message": "Added to waitlist", "appointment_id": new_appt.id}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _assert_access(user, appt: Appointment):
    from healthcare.models.patient import Patient
    if isinstance(user, Patient) and appt.patient_id != user.id:
        raise HTTPException(403, "Access denied")


def _schedule_notifications(appt: Appointment):
    """Enqueue Celery tasks to send appointment reminders."""
    try:
        from healthcare.workers.appointment_worker import send_appointment_reminder
        # 24-hour reminder
        run_at = appt.scheduled_start - timedelta(hours=24)
        send_appointment_reminder.apply_async(
            args=[appt.id, "24h"],
            eta=run_at,
        )
        # 1-hour reminder
        run_at_1h = appt.scheduled_start - timedelta(hours=1)
        send_appointment_reminder.apply_async(
            args=[appt.id, "1h"],
            eta=run_at_1h,
        )
    except Exception:
        pass  # Celery may not be running in all environments


def _create_recurrences(db: Session, parent: Appointment, body: AppointmentCreate):
    """Create child recurring appointments."""
    delta_map = {
        RecurrencePattern.daily: timedelta(days=1),
        RecurrencePattern.weekly: timedelta(weeks=1),
        RecurrencePattern.biweekly: timedelta(weeks=2),
        RecurrencePattern.monthly: timedelta(days=30),
    }
    delta = delta_map.get(body.recurrence)
    if not delta:
        return

    current_start = parent.scheduled_start + delta
    end_date = body.recurrence_end_date.replace(tzinfo=None)

    while current_start <= end_date:
        end = current_start + timedelta(
            minutes=(parent.scheduled_end - parent.scheduled_start).seconds // 60
        )
        child = Appointment(
            patient_id=parent.patient_id,
            provider_id=parent.provider_id,
            department_id=parent.department_id,
            scheduled_start=current_start,
            scheduled_end=end,
            appointment_type=parent.appointment_type,
            status=AppointmentStatus.scheduled,
            reason=parent.reason,
            recurrence=body.recurrence,
            parent_appointment_id=parent.id,
        )
        db.add(child)
        current_start += delta
