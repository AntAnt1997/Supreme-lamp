"""
Entry point for the AI Healthcare Management Platform.

Usage:
    # Start the platform (API + patient portal)
    python -m healthcare.main

    # Start Celery worker (24/7 background workflows)
    celery -A healthcare.workers.celery_app worker --loglevel=info

    # Start Celery Beat scheduler (periodic tasks)
    celery -A healthcare.workers.celery_app beat --loglevel=info
"""

import logging
import signal
import sys

import uvicorn

from healthcare.config import healthcare_settings

logging.basicConfig(
    level=logging.DEBUG if healthcare_settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("healthcare.log", mode="a"),
    ],
)
logger = logging.getLogger("healthcare")


def main():
    logger.info("=" * 60)
    logger.info("AI HEALTHCARE MANAGEMENT PLATFORM")
    logger.info("Host: %s  Port: %d", healthcare_settings.app_host, healthcare_settings.app_port)
    logger.info("Docs: http://%s:%d/docs", healthcare_settings.app_host, healthcare_settings.app_port)
    logger.info("=" * 60)

    from healthcare.app import create_app
    app = create_app()

    uvicorn.run(
        app,
        host=healthcare_settings.app_host,
        port=healthcare_settings.app_port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
