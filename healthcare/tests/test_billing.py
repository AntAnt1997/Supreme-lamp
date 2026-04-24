"""Tests for billing routes and payment service."""

import pytest
from datetime import datetime, timedelta, timezone


def _register_and_login(client, email="billtest@example.com"):
    client.post("/api/auth/register/patient", json={
        "email": email,
        "password": "Pass1234",
        "first_name": "Bill",
        "last_name": "Test",
        "date_of_birth": "1990-01-01",
    })
    r = client.post("/api/auth/token", data={"username": email, "password": "Pass1234"})
    return r.json()


def _register_staff(client, email="staff@example.com"):
    client.post("/api/auth/register/staff", json={
        "email": email,
        "password": "StaffPass1",
        "first_name": "Dr",
        "last_name": "Admin",
        "role": "admin",
    })
    r = client.post("/api/auth/token", data={"username": email, "password": "StaffPass1"})
    return r.json()


def test_patient_can_list_empty_bills(client):
    login = _register_and_login(client, "empty@example.com")
    token = login["access_token"]
    resp = client.get("/api/billing/bills", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_bill_requires_staff(client):
    login = _register_and_login(client, "patient2@example.com")
    token = login["access_token"]
    resp = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {token}"},
        json={"patient_id": login["user_id"], "line_items": [{"description": "Visit", "amount": 100.0}]},
    )
    assert resp.status_code == 403


def test_staff_creates_bill(client):
    patient = _register_and_login(client, "patient3@example.com")
    staff = _register_staff(client, "staff3@example.com")

    resp = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {staff['access_token']}"},
        json={
            "patient_id": patient["user_id"],
            "line_items": [
                {"description": "Office Visit", "code": "99213", "amount": 150.0},
                {"description": "Lab Work", "code": "80048", "amount": 75.0},
            ],
            "insurance_adjustment": 100.0,
            "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subtotal"] == 225.0
    assert data["insurance_adjustment"] == 100.0
    assert data["total"] == 125.0
    assert data["balance_due"] == 125.0
    assert data["status"] == "issued"


def test_patient_views_own_bill(client):
    patient = _register_and_login(client, "patient4@example.com")
    staff = _register_staff(client, "staff4@example.com")

    bill = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {staff['access_token']}"},
        json={"patient_id": patient["user_id"],
              "line_items": [{"description": "Test", "amount": 50.0}]},
    ).json()

    resp = client.get(f"/api/billing/bills/{bill['id']}",
        headers={"Authorization": f"Bearer {patient['access_token']}"})
    assert resp.status_code == 200


def test_make_payment_reduces_balance(client):
    patient = _register_and_login(client, "patient5@example.com")
    staff = _register_staff(client, "staff5@example.com")

    bill = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {staff['access_token']}"},
        json={"patient_id": patient["user_id"],
              "line_items": [{"description": "Procedure", "amount": 200.0}]},
    ).json()

    pay_resp = client.post("/api/billing/payments",
        headers={"Authorization": f"Bearer {patient['access_token']}"},
        json={"bill_id": bill["id"], "amount": 100.0, "method": "cash"},
    )
    assert pay_resp.status_code == 201
    data = pay_resp.json()
    assert data["status"] == "succeeded"
    assert data["amount"] == 100.0


def test_payment_plan_setup(client):
    patient = _register_and_login(client, "patient6@example.com")
    staff = _register_staff(client, "staff6@example.com")

    bill = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {staff['access_token']}"},
        json={"patient_id": patient["user_id"],
              "line_items": [{"description": "Surgery", "amount": 3000.0}]},
    ).json()

    plan_resp = client.post("/api/billing/payments/plan",
        headers={"Authorization": f"Bearer {patient['access_token']}"},
        json={"bill_id": bill["id"], "months": 12},
    )
    assert plan_resp.status_code == 200
    data = plan_resp.json()
    assert data["months"] == 12
    assert abs(data["monthly_payment"] - 250.0) < 0.01


def test_payment_exceeding_balance_rejected(client):
    patient = _register_and_login(client, "patient7@example.com")
    staff = _register_staff(client, "staff7@example.com")

    bill = client.post("/api/billing/bills",
        headers={"Authorization": f"Bearer {staff['access_token']}"},
        json={"patient_id": patient["user_id"],
              "line_items": [{"description": "Visit", "amount": 50.0}]},
    ).json()

    pay_resp = client.post("/api/billing/payments",
        headers={"Authorization": f"Bearer {patient['access_token']}"},
        json={"bill_id": bill["id"], "amount": 999.0, "method": "cash"},
    )
    assert pay_resp.status_code == 400
