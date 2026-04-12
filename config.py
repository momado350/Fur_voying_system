import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url: str | None) -> str:
    if not url:
        return "sqlite:///app.db"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URI")
        or "sqlite:///app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))

    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").strip().lower()
    UPLOAD_BASE = os.getenv("UPLOAD_BASE", "static/uploads")
    RESUME_FOLDER = os.path.join(UPLOAD_BASE, "resumes")
    PHOTO_FOLDER = os.path.join(UPLOAD_BASE, "photos")

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_REGION = os.getenv("AWS_S3_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", os.getenv("S3_BUCKET"))
    S3_RESUME_PREFIX = os.getenv("S3_RESUME_PREFIX", "resumes")
    S3_PHOTO_PREFIX = os.getenv("S3_PHOTO_PREFIX", "photos")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
