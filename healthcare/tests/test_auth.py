"""Tests for authentication routes."""

import pytest


def test_register_patient(client):
    resp = client.post("/api/auth/register/patient", json={
        "email": "alice@example.com",
        "password": "Password123",
        "first_name": "Alice",
        "last_name": "Smith",
        "date_of_birth": "1990-05-15",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "patient"
    assert "access_token" in data
    assert data["user_id"] > 0


def test_register_duplicate_email(client):
    payload = {
        "email": "bob@example.com",
        "password": "Password123",
        "first_name": "Bob",
        "last_name": "Jones",
        "date_of_birth": "1985-01-01",
    }
    client.post("/api/auth/register/patient", json=payload)
    resp = client.post("/api/auth/register/patient", json=payload)
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/auth/register/patient", json={
        "email": "carol@example.com",
        "password": "P@ssword1",
        "first_name": "Carol",
        "last_name": "White",
        "date_of_birth": "1992-03-20",
    })
    resp = client.post("/api/auth/token", data={
        "username": "carol@example.com",
        "password": "P@ssword1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "patient"


def test_login_wrong_password(client):
    client.post("/api/auth/register/patient", json={
        "email": "dave@example.com",
        "password": "GoodPass1",
        "first_name": "Dave",
        "last_name": "Brown",
        "date_of_birth": "1980-07-10",
    })
    resp = client.post("/api/auth/token", data={
        "username": "dave@example.com",
        "password": "WrongPass",
    })
    assert resp.status_code == 401


def test_get_me(client):
    client.post("/api/auth/register/patient", json={
        "email": "eve@example.com",
        "password": "MyPass123",
        "first_name": "Eve",
        "last_name": "Green",
        "date_of_birth": "1995-11-30",
    })
    login = client.post("/api/auth/token", data={
        "username": "eve@example.com", "password": "MyPass123"
    })
    token = login.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "eve@example.com"
    assert data["role"] == "patient"


def test_protected_route_no_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
