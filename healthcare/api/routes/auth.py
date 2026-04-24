"""Auth API routes – patient/staff registration, login, MFA."""

import logging
import secrets
from datetime import date
from typing import Optional

import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from healthcare.api.auth_utils import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from healthcare.database.db import get_db
from healthcare.models.patient import Patient, PatientStatus, Gender
from healthcare.models.provider import Provider, StaffRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / Response schemas ─────────────────────────────────────────────────

class PatientRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone: Optional[str] = None
    gender: Optional[Gender] = None


class StaffRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: StaffRole = StaffRole.physician
    department_id: Optional[int] = None
    npi_number: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_url: str


class MFAVerifyRequest(BaseModel):
    code: str


# ── Patient Registration ───────────────────────────────────────────────────────

@router.post("/register/patient", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_patient(body: PatientRegister, db: Session = Depends(get_db)):
    if db.query(Patient).filter(Patient.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    patient = Patient(
        email=body.email,
        hashed_password=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        date_of_birth=body.date_of_birth,
        phone=body.phone,
        gender=body.gender,
        status=PatientStatus.active,
    )
    db.add(patient)
    db.flush()

    token = create_access_token(subject=patient.email, role="patient")
    return TokenResponse(access_token=token, role="patient", user_id=patient.id)


# ── Staff Registration ─────────────────────────────────────────────────────────

@router.post("/register/staff", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_staff(body: StaffRegister, db: Session = Depends(get_db)):
    if db.query(Provider).filter(Provider.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    provider = Provider(
        email=body.email,
        hashed_password=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        department_id=body.department_id,
        npi_number=body.npi_number,
    )
    db.add(provider)
    db.flush()

    token = create_access_token(subject=provider.email, role=provider.role.value)
    return TokenResponse(access_token=token, role=provider.role.value, user_id=provider.id)


# ── Token (Login) ─────────────────────────────────────────────────────────────

@router.post("/token", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Try patient first, then provider
    user = db.query(Patient).filter(Patient.email == form.username).first()
    role = "patient"
    if user is None:
        user = db.query(Provider).filter(Provider.email == form.username).first()
        if user:
            role = user.role.value

    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If MFA is enabled, the token is not fully authenticated yet – client must call /verify-mfa
    if user.mfa_enabled:
        # Issue a short-lived pre-auth token
        token = create_access_token(subject=user.email, role=role, expires_minutes=5)
        return TokenResponse(access_token=token, role="mfa_required", user_id=user.id)

    token = create_access_token(subject=user.email, role=role)
    return TokenResponse(access_token=token, role=role, user_id=user.id)


# ── MFA Setup ─────────────────────────────────────────────────────────────────

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(current_user=Depends(get_current_user)):
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    # Note: caller must call /mfa/enable after verifying a code to activate MFA
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_user.email,
        issuer_name="Healthcare Platform",
    )
    return MFASetupResponse(
        secret=secret,
        provisioning_uri=uri,
        qr_code_url=f"https://api.qrserver.com/v1/create-qr-code/?data={uri}&size=200x200",
    )


@router.post("/mfa/enable")
def enable_mfa(body: MFAVerifyRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.mfa_secret:
        raise HTTPException(400, "MFA not set up. Call /mfa/setup first.")
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(body.code):
        raise HTTPException(400, "Invalid MFA code")
    current_user.mfa_enabled = True
    db.add(current_user)
    return {"message": "MFA enabled successfully"}


@router.post("/mfa/verify", response_model=TokenResponse)
def verify_mfa(
    body: MFAVerifyRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(400, "MFA not enabled for this account")
    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(body.code):
        raise HTTPException(400, "Invalid MFA code")

    role = "patient" if isinstance(current_user, Patient) else current_user.role.value
    token = create_access_token(subject=current_user.email, role=role)
    return TokenResponse(access_token=token, role=role, user_id=current_user.id)


# ── Profile ────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    if isinstance(current_user, Patient):
        return {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": "patient",
            "mfa_enabled": current_user.mfa_enabled,
        }
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "mfa_enabled": current_user.mfa_enabled,
        "department_id": current_user.department_id,
    }
