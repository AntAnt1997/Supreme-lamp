"""FastAPI application factory for the Healthcare Platform."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from healthcare.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from healthcare.api.routes import auth, appointments, billing, ai_chat, departments
from healthcare.dashboard.app import create_dashboard_routes

logger = logging.getLogger(__name__)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "dashboard", "static")
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "dashboard", "templates")


def create_app() -> FastAPI:
    """Create and configure the Healthcare FastAPI application."""

    app = FastAPI(
        title="AI Healthcare Management Platform",
        description=(
            "24/7 AI-powered healthcare platform with appointments, "
            "billing, and full medical department coverage."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ─────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # ── API Routes ─────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(appointments.router)
    app.include_router(billing.router)
    app.include_router(ai_chat.router)
    app.include_router(departments.router)

    # ── Static files ───────────────────────────────────
    if os.path.isdir(STATIC_DIR):
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # ── Dashboard (HTML portal) ────────────────────────
    templates = Jinja2Templates(directory=TEMPLATE_DIR)
    create_dashboard_routes(app, templates)

    # ── Startup event ──────────────────────────────────
    @app.on_event("startup")
    async def on_startup():
        from healthcare.database.db import init_db
        from healthcare.config import healthcare_settings
        init_db(healthcare_settings.database_url)
        logger.info("Healthcare database initialized")

        # Auto-seed departments
        from healthcare.database.db import get_session
        from healthcare.models.department import Department, ALL_DEPARTMENTS
        with get_session() as db:
            if db.query(Department).count() == 0:
                for d in ALL_DEPARTMENTS:
                    db.add(Department(
                        name=d["name"],
                        category=d["category"],
                        description=d["description"],
                    ))
        logger.info("Departments seeded")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "Healthcare Platform"}

    return app
