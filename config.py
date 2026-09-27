"""
Application configuration.

All values are read from environment variables. Never hardcode credentials
here. In production (EC2), these variables are supplied via an EnvironmentFile
loaded by systemd (see deploy/flaskapp.service). Locally, they are loaded from
a .env file (see .env.example) that is never committed to git.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str, default: str = None) -> str:
    value = os.environ.get(name, default)
    return value


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB

    # Database (RDS MySQL) — credentials only ever come from the environment
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME", "studentdb")

    # S3
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    PRESIGNED_URL_EXPIRY_SECONDS = int(os.environ.get("PRESIGNED_URL_EXPIRY_SECONDS", 3600))

    # Upload validation
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/gif"}


def validate_config():
    """Fail fast and loudly at startup if required config is missing,
    instead of failing confusingly on the first request."""
    missing = []
    for key in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "S3_BUCKET_NAME", "AWS_REGION"):
        if not getattr(Config, key):
            missing.append(key)
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in real values."
        )
