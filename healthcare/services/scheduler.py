"""Appointment scheduling service – slot availability engine."""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


def get_available_slots(db, provider, target_date_str: str) -> List[Dict]:
    """
    Return a list of available time slots for a provider on the given date.
    target_date_str: "YYYY-MM-DD"
    """
    from healthcare.models.appointment import Appointment, AppointmentStatus

    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        raise ValueError(f"Invalid date format: {target_date_str}. Use YYYY-MM-DD.")

    day_name = target_date.strftime("%A").lower()  # e.g. "monday"
    schedule_template = provider.schedule_template or {}
    day_schedule = schedule_template.get(day_name, [])

    if not day_schedule:
        return []  # Provider not available on this day

    slot_duration = provider.slot_duration_minutes or 30
    slots = []

    # Generate all possible slots from the schedule template
    for block in day_schedule:
        start_time = datetime.strptime(f"{target_date_str} {block['start']}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{target_date_str} {block['end']}", "%Y-%m-%d %H:%M")
        current = start_time
        while current + timedelta(minutes=slot_duration) <= end_time:
            slots.append(current)
            current += timedelta(minutes=slot_duration)

    # Load existing booked appointments for this provider on this date
    day_start = datetime.combine(target_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)
    booked = db.query(Appointment).filter(
        Appointment.provider_id == provider.id,
        Appointment.scheduled_start >= day_start,
        Appointment.scheduled_start < day_end,
        Appointment.status.not_in([AppointmentStatus.cancelled, AppointmentStatus.no_show]),
    ).all()

    booked_starts = {a.scheduled_start for a in booked}

    available = []
    now = datetime.now()
    for slot_start in slots:
        if slot_start <= now:
            continue  # Skip past slots
        if slot_start in booked_starts:
            continue
        slot_end = slot_start + timedelta(minutes=slot_duration)
        available.append({
            "start": slot_start.isoformat(),
            "end": slot_end.isoformat(),
            "duration_minutes": slot_duration,
        })

    return available


def get_next_available_slot(db, provider, days_ahead: int = 30) -> Dict | None:
    """Find the earliest available slot within the next `days_ahead` days."""
    from datetime import date as date_type
    today = date_type.today()
    for offset in range(1, days_ahead + 1):
        target = today + timedelta(days=offset)
        slots = get_available_slots(db, provider, target.isoformat())
        if slots:
            return {"date": target.isoformat(), **slots[0]}
    return None
