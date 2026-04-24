"""Healthcare platform configuration (loaded from environment variables)."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, str(default)))


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


@dataclass
class HealthcareSettings:
    # Database
    database_url: str = field(default_factory=lambda: _env("HEALTHCARE_DATABASE_URL", "sqlite:///healthcare.db"))

    # App
    app_host: str = field(default_factory=lambda: _env("HEALTHCARE_HOST", "0.0.0.0"))
    app_port: int = field(default_factory=lambda: _env_int("HEALTHCARE_PORT", 8090))
    secret_key: str = field(default_factory=lambda: _env("HEALTHCARE_SECRET_KEY", "change-me-healthcare"))
    debug: bool = field(default_factory=lambda: _env_bool("HEALTHCARE_DEBUG", False))

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = field(default_factory=lambda: _env_int("JWT_EXPIRE_MINUTES", 60))

    # AI / LLM
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4o-mini"))

    # Celery / Redis
    redis_url: str = field(default_factory=lambda: _env("REDIS_URL", "redis://localhost:6379/0"))
    celery_broker_url: str = field(default_factory=lambda: _env("CELERY_BROKER_URL", "redis://localhost:6379/1"))
    celery_result_backend: str = field(default_factory=lambda: _env("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"))

    # Stripe
    stripe_secret_key: str = field(default_factory=lambda: _env("STRIPE_SECRET_KEY"))
    stripe_publishable_key: str = field(default_factory=lambda: _env("STRIPE_PUBLISHABLE_KEY"))
    stripe_webhook_secret: str = field(default_factory=lambda: _env("STRIPE_WEBHOOK_SECRET"))

    # Twilio (SMS)
    twilio_account_sid: str = field(default_factory=lambda: _env("TWILIO_ACCOUNT_SID"))
    twilio_auth_token: str = field(default_factory=lambda: _env("TWILIO_AUTH_TOKEN"))
    twilio_from_number: str = field(default_factory=lambda: _env("TWILIO_FROM_NUMBER"))

    # SendGrid (Email)
    sendgrid_api_key: str = field(default_factory=lambda: _env("SENDGRID_API_KEY"))
    from_email: str = field(default_factory=lambda: _env("FROM_EMAIL", "noreply@healthcare.local"))
    from_name: str = field(default_factory=lambda: _env("FROM_NAME", "Healthcare Platform"))

    # App URL (used in notification links)
    app_base_url: str = field(default_factory=lambda: _env("HEALTHCARE_BASE_URL", "http://localhost:8090"))


# Singleton
healthcare_settings = HealthcareSettings()
