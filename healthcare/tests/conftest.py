"""Shared pytest fixtures for healthcare platform tests."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure env is set before any healthcare module is imported
os.environ.setdefault("HEALTHCARE_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("HEALTHCARE_SECRET_KEY", "test-secret-key-for-testing")

from healthcare.models.base import Base  # noqa: F401
import healthcare.models.department     # noqa: F401
import healthcare.models.patient        # noqa: F401
import healthcare.models.provider       # noqa: F401
import healthcare.models.appointment    # noqa: F401
import healthcare.models.billing        # noqa: F401
import healthcare.models.ai_conversation # noqa: F401
import healthcare.models.notification   # noqa: F401

# Single shared engine – StaticPool keeps one connection so all sessions share the same in-memory DB
_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_TEST_ENGINE)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)


@pytest.fixture(scope="session")
def db_engine():
    yield _TEST_ENGINE


@pytest.fixture
def db_session():
    session = _TestSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client():
    """FastAPI TestClient backed by the shared in-memory database."""
    import healthcare.database.db as db_module
    db_module._engine = _TEST_ENGINE
    db_module._SessionLocal = _TestSessionLocal

    from healthcare.app import create_app
    app = create_app()

    from healthcare.database.db import get_db

    def override_get_db():
        session = _TestSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
