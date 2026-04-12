import os
import uuid
from flask import current_app, url_for
from werkzeug.utils import secure_filename

from s3_utils import upload_file_to_s3

ALLOWED_RESUME = {"pdf", "doc", "docx"}
ALLOWED_IMAGE = {"png", "jpg", "jpeg", "webp"}


def ext_ok(filename: str, allowed: set[str]) -> bool:
    if "." not in filename:
        return False
    return filename.rsplit(".", 1)[1].lower() in allowed


def _new_name(filename: str) -> str:
    original = secure_filename(filename or "")
    ext = original.rsplit(".", 1)[1].lower() if "." in original else "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def _local_rel_path(kind: str, filename: str) -> str:
    folder = current_app.config["RESUME_FOLDER"] if kind == "resume" else current_app.config["PHOTO_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename).replace("\\", "/")


def _s3_key(kind: str, filename: str) -> str:
    prefix = current_app.config["S3_RESUME_PREFIX"] if kind == "resume" else current_app.config["S3_PHOTO_PREFIX"]
    cleaned_prefix = (prefix or "").strip("/")
    if cleaned_prefix:
        return f"{cleaned_prefix}/{filename}"
    return filename


def save_upload(file_storage, kind: str) -> str:
    filename = _new_name(file_storage.filename or "upload.bin")
    backend = current_app.config.get("STORAGE_BACKEND", "local")

    if backend == "s3":
        key = _s3_key(kind, filename)
        return upload_file_to_s3(file_storage, key, current_app.config)

    rel_path = _local_rel_path(kind, filename)
    file_storage.save(rel_path)
    return rel_path


def file_url(value: str | None, *, download: bool = False) -> str | None:
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value

    cleaned = value.replace("\\", "/")
    if cleaned.startswith("static/"):
        cleaned = cleaned[len("static/"):]
    return url_for("static", filename=cleaned)
