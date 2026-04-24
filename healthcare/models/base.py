"""Shared SQLAlchemy declarative base for all healthcare models."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at / updated_at columns to any model."""
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)
