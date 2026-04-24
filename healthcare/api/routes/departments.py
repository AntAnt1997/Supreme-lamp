"""Departments & Providers API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from healthcare.api.auth_utils import get_current_user, require_admin
from healthcare.database.db import get_db
from healthcare.models.department import Department, Specialty, ALL_DEPARTMENTS
from healthcare.models.provider import Provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["departments", "providers"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class DepartmentOut(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str]
    floor_location: Optional[str]
    phone: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ProviderOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    display_title: str
    role: str
    department_id: Optional[int]
    bio: Optional[str]
    photo_url: Optional[str]
    telehealth_available: bool
    in_person_available: bool
    accepted_insurance: list
    languages: list
    board_certifications: list
    average_rating: float
    slot_duration_minutes: int
    is_active: bool

    class Config:
        from_attributes = True


# ── Department Endpoints ───────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentOut])
def list_departments(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Department).filter(Department.is_active == True)
    if category:
        query = query.filter(Department.category == category)
    return query.order_by(Department.name).all()


@router.get("/departments/{dept_id}", response_model=DepartmentOut)
def get_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(404, "Department not found")
    return dept


@router.post("/departments/seed", status_code=201)
def seed_departments(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Seed all departments from the master list (admin only)."""
    added = 0
    for d in ALL_DEPARTMENTS:
        exists = db.query(Department).filter(Department.name == d["name"]).first()
        if not exists:
            db.add(Department(name=d["name"], category=d["category"], description=d["description"]))
            added += 1
    db.flush()
    return {"message": f"Seeded {added} departments"}


@router.get("/departments/seed/auto", status_code=201)
def auto_seed_departments(db: Session = Depends(get_db)):
    """Auto-seed departments on first run (no auth required – idempotent)."""
    added = 0
    for d in ALL_DEPARTMENTS:
        exists = db.query(Department).filter(Department.name == d["name"]).first()
        if not exists:
            db.add(Department(name=d["name"], category=d["category"], description=d["description"]))
            added += 1
    db.flush()
    return {"message": f"Seeded {added} departments", "total": len(ALL_DEPARTMENTS)}


# ── Provider Endpoints ─────────────────────────────────────────────────────────

@router.get("/providers", response_model=List[ProviderOut])
def list_providers(
    department_id: Optional[int] = None,
    insurance: Optional[str] = None,
    telehealth: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
):
    query = db.query(Provider).filter(Provider.is_active == True)
    if department_id:
        query = query.filter(Provider.department_id == department_id)
    if telehealth is not None:
        query = query.filter(Provider.telehealth_available == telehealth)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Provider.first_name.ilike(term)) | (Provider.last_name.ilike(term))
        )
    providers = query.order_by(Provider.last_name).all()
    if insurance:
        # Filter in Python since JSON column search varies by DB
        providers = [p for p in providers if insurance in (p.accepted_insurance or [])]
    return providers


@router.get("/providers/{provider_id}", response_model=ProviderOut)
def get_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")
    return provider


@router.get("/providers/{provider_id}/availability")
def get_provider_availability(
    provider_id: int,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """Return available time slots for a provider on a given date."""
    from healthcare.services.scheduler import get_available_slots
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404, "Provider not found")
    try:
        slots = get_available_slots(db, provider, date)
        return {"provider_id": provider_id, "date": date, "slots": slots}
    except ValueError as e:
        raise HTTPException(400, str(e))
