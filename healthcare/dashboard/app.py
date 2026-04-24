"""Dashboard route registration – serves HTML patient portal pages."""

import logging
import os

from fastapi import Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)


def create_dashboard_routes(app, templates):
    """Register HTML page routes on the FastAPI app."""

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def portal_home(request: Request):
        return templates.TemplateResponse(request, "index.html")

    @app.get("/appointments", response_class=HTMLResponse, include_in_schema=False)
    async def portal_appointments(request: Request):
        return templates.TemplateResponse(request, "appointments.html")

    @app.get("/billing", response_class=HTMLResponse, include_in_schema=False)
    async def portal_billing(request: Request):
        return templates.TemplateResponse(request, "billing.html")

    @app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
    async def portal_chat(request: Request):
        return templates.TemplateResponse(request, "chat.html")
