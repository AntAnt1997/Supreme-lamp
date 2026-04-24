"""Tests for appointment scheduling."""

import pytest
from datetime import datetime, timedelta, timezone


def _register_patient(client, email):
    client.post("/api/auth/register/patient", json={
        "email": email, "password": "Pass123!", "first_name": "Test", "last_name": "Patient",
        "date_of_birth": "1990-01-01",
    })
    r = client.post("/api/auth/token", data={"username": email, "password": "Pass123!"})
    return r.json()


def _register_provider(client, db_session, dept_id=None):
    """Create a provider directly in the DB and return it."""
    from healthcare.models.provider import Provider
    from healthcare.api.auth_utils import hash_password
    from datetime import date

    # Get or use first department id
    if dept_id is None:
        from healthcare.models.department import Department
        dept = db_session.query(Department).first()
        dept_id = dept.id if dept else None

    provider = Provider(
        email=f"provider_{id(db_session)}@example.com",
        hashed_password=hash_password("DocPass1"),
        first_name="Dr",
        last_name="Test",
        department_id=dept_id,
        slot_duration_minutes=30,
        telehealth_available=True,
        in_person_available=True,
        schedule_template={
            "monday": [{"start": "09:00", "end": "17:00"}],
            "tuesday": [{"start": "09:00", "end": "17:00"}],
            "wednesday": [{"start": "09:00", "end": "17:00"}],
            "thursday": [{"start": "09:00", "end": "17:00"}],
            "friday": [{"start": "09:00", "end": "17:00"}],
        },
    )
    db_session.add(provider)
    db_session.commit()
    return provider


def test_list_appointments_empty(client):
    patient = _register_patient(client, "appt1@example.com")
    resp = client.get("/api/appointments/",
        headers={"Authorization": f"Bearer {patient['access_token']}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_scheduler_get_available_slots(db_session):
    from healthcare.models.provider import Provider
    from healthcare.api.auth_utils import hash_password
    from healthcare.services.scheduler import get_available_slots
    from datetime import date

    provider = Provider(
        email="sched_test@example.com",
        hashed_password=hash_password("x"),
        first_name="A",
        last_name="B",
        slot_duration_minutes=30,
        schedule_template={
            "monday": [{"start": "09:00", "end": "11:00"}],
        },
    )
    db_session.add(provider)
    db_session.commit()

    # Find next Monday
    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    next_monday = today + timedelta(days=days_until_monday)

    slots = get_available_slots(db_session, provider, next_monday.isoformat())
    # 2-hour window / 30-min slots = 4 slots
    assert len(slots) == 4
    assert "start" in slots[0]
    assert "end" in slots[0]


def test_scheduler_no_slots_on_day_off(db_session):
    from healthcare.models.provider import Provider
    from healthcare.api.auth_utils import hash_password
    from healthcare.services.scheduler import get_available_slots
    from datetime import date

    provider = Provider(
        email="sched_test2@example.com",
        hashed_password=hash_password("x"),
        first_name="C",
        last_name="D",
        slot_duration_minutes=30,
        schedule_template={"monday": [{"start": "09:00", "end": "17:00"}]},
    )
    db_session.add(provider)
    db_session.commit()

    # Find next Sunday (no schedule)
    today = date.today()
    days_until_sunday = (6 - today.weekday()) % 7 or 7
    next_sunday = today + timedelta(days=days_until_sunday)

    slots = get_available_slots(db_session, provider, next_sunday.isoformat())
    assert slots == []


def test_scheduler_invalid_date(db_session):
    from healthcare.models.provider import Provider
    from healthcare.api.auth_utils import hash_password
    from healthcare.services.scheduler import get_available_slots

    provider = Provider(
        email="sched_test3@example.com",
        hashed_password=hash_password("x"),
        first_name="E",
        last_name="F",
    )
    db_session.add(provider)
    db_session.commit()

    with pytest.raises(ValueError):
        get_available_slots(db_session, provider, "not-a-date")
