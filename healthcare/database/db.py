"""Database setup and session management for the healthcare platform."""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from healthcare.models.base import Base  # noqa: F401 – imported so all models register
import healthcare.models.department  # noqa: F401
import healthcare.models.patient  # noqa: F401
import healthcare.models.provider  # noqa: F401
import healthcare.models.appointment  # noqa: F401
import healthcare.models.billing  # noqa: F401
import healthcare.models.ai_conversation  # noqa: F401
import healthcare.models.notification  # noqa: F401

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = os.getenv("HEALTHCARE_DATABASE_URL", "sqlite:///healthcare.db")
        kwargs = {}
        if db_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(db_url, **kwargs)
        # Enable WAL mode for SQLite (better concurrent read performance)
        if db_url.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def set_wal(dbapi_con, _):
                dbapi_con.execute("PRAGMA journal_mode=WAL")
                dbapi_con.execute("PRAGMA foreign_keys=ON")
    return _engine


def init_db(database_url: str | None = None) -> None:
    """Create all tables in the database."""
    if database_url:
        os.environ["HEALTHCARE_DATABASE_URL"] = database_url
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context-manager that yields a database session and handles commit/rollback."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
