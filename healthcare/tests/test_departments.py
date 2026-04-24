"""Tests for department and provider endpoints."""

import pytest


def _seed_department(client, admin_token):
    # Auto-seed without auth
    resp = client.get("/api/departments/seed/auto")
    return resp


def test_list_departments_auto_seeded(client):
    # Departments are seeded on startup
    resp = client.get("/api/departments")
    assert resp.status_code == 200
    depts = resp.json()
    assert len(depts) > 0
    names = [d["name"] for d in depts]
    assert "Primary Care" in names
    assert "General Dentistry" in names
    assert "Emergency Medicine" in names
    assert "Cardiology" in names
    assert "Psychiatry" in names


def test_department_categories_present(client):
    resp = client.get("/api/departments")
    depts = resp.json()
    categories = {d["category"] for d in depts}
    expected = {"primary_care", "dentistry", "emergency", "cardiovascular",
                "behavioral_health", "oncology", "rehabilitation", "specialty"}
    assert expected.issubset(categories)


def test_filter_departments_by_category(client):
    resp = client.get("/api/departments?category=dentistry")
    assert resp.status_code == 200
    depts = resp.json()
    assert all(d["category"] == "dentistry" for d in depts)
    assert len(depts) >= 4  # At least 4 dental departments


def test_get_department_by_id(client):
    all_depts = client.get("/api/departments").json()
    first = all_depts[0]
    resp = client.get(f"/api/departments/{first['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == first["id"]


def test_get_department_not_found(client):
    resp = client.get("/api/departments/999999")
    assert resp.status_code == 404


def test_list_providers_empty(client):
    resp = client.get("/api/providers")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
