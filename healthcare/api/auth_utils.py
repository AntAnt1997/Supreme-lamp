"""JWT-based authentication utilities for the healthcare platform."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from healthcare.config import healthcare_settings

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT helpers ────────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    role: str = "patient",
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or healthcare_settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        healthcare_settings.secret_key,
        algorithm=healthcare_settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(
        token,
        healthcare_settings.secret_key,
        algorithms=[healthcare_settings.jwt_algorithm],
    )


# ── FastAPI dependency helpers ─────────────────────────────────────────────────

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from healthcare.database.db import get_db

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
):
    """FastAPI dependency – returns the authenticated Patient or Provider."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject: str = payload.get("sub")
        role: str = payload.get("role", "patient")
        if subject is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # Lazy imports to avoid circular dependencies
    if role == "patient":
        from healthcare.models.patient import Patient
        user = db.query(Patient).filter(Patient.email == subject).first()
    else:
        from healthcare.models.provider import Provider
        user = db.query(Provider).filter(Provider.email == subject).first()

    if user is None:
        raise credentials_exc
    return user


def require_staff(current_user=Depends(get_current_user)):
    """Dependency that ensures the caller is a provider/staff member."""
    from healthcare.models.provider import Provider
    if not isinstance(current_user, Provider):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff only")
    return current_user


def require_admin(current_user=Depends(get_current_user)):
    """Dependency that ensures the caller has the admin role."""
    from healthcare.models.provider import Provider, StaffRole
    if not isinstance(current_user, Provider) or current_user.role != StaffRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
