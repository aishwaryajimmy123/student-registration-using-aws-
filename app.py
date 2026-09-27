"""
Flask Student Registration application.

Flow:
  GET  /            -> render registration form
  POST /register     -> validate input, upload photo to S3 (via EC2 IAM role
                         credentials, discovered automatically by boto3),
                         insert student record into RDS MySQL, render success
                         page with a time-limited pre-signed URL to the photo.

Security notes:
  - No AWS access keys anywhere in this code. boto3.client("s3") picks up
    credentials automatically from the EC2 instance metadata service via the
    attached IAM instance role.
  - DB credentials come only from environment variables (config.py).
  - SQL uses parameterized queries exclusively.
  - Uploaded filenames are replaced with a generated UUID-based name; the
    original filename is never used to build a path.
  - Internal exceptions are logged server-side and never shown to the client.
"""

import logging
import os
import re
import uuid

import boto3
import pymysql
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, render_template, request, redirect, url_for, flash

from config import Config, validate_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("studentapp")

app = Flask(__name__)
app.config.from_object(Config)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_s3_client = None


def get_s3_client():
    """Lazily create a boto3 S3 client. Credentials are discovered
    automatically from the EC2 instance's IAM role — never hardcoded."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=app.config["AWS_REGION"])
    return _s3_client


def get_db_connection():
    """Open a new PyMySQL connection using environment-sourced credentials."""
    return pymysql.connect(
        host=app.config["DB_HOST"],
        port=app.config["DB_PORT"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        autocommit=True,
    )


def allowed_file(filename: str, mimetype: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in app.config["ALLOWED_EXTENSIONS"] and mimetype in app.config["ALLOWED_MIME_TYPES"]


def build_safe_object_key(original_filename: str) -> str:
    """Generate a unique, safe S3 object key. Never derive the path from
    user-supplied input beyond the file extension."""
    ext = original_filename.rsplit(".", 1)[1].lower()
    return f"student-photos/{uuid.uuid4().hex}.{ext}"


def validate_registration_form(form, files):
    errors = []

    name = (form.get("name") or "").strip()
    email = (form.get("email") or "").strip()
    course = (form.get("course") or "").strip()
    photo = files.get("photo")

    if not name:
        errors.append("Name is required.")
    elif len(name) > 100:
        errors.append("Name must be 100 characters or fewer.")

    if not email:
        errors.append("Email is required.")
    elif not EMAIL_RE.match(email) or len(email) > 150:
        errors.append("A valid email address is required.")

    if not course:
        errors.append("Course is required.")
    elif len(course) > 100:
        errors.append("Course must be 100 characters or fewer.")

    if not photo or photo.filename == "":
        errors.append("A photo is required.")
    elif not allowed_file(photo.filename, photo.mimetype):
        errors.append("Photo must be a PNG, JPG, or GIF image.")

    return name, email, course, photo, errors


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    name, email, course, photo, errors = validate_registration_form(request.form, request.files)

    if errors:
        for error in errors:
            flash(error, "error")
        return redirect(url_for("index"))

    object_key = build_safe_object_key(photo.filename)

    try:
        s3 = get_s3_client()
        s3.upload_fileobj(
            photo,
            app.config["S3_BUCKET_NAME"],
            object_key,
            ExtraArgs={"ContentType": photo.mimetype},
        )
    except (BotoCoreError, ClientError):
        logger.exception("S3 upload failed")
        flash("We could not upload your photo right now. Please try again shortly.", "error")
        return redirect(url_for("index"))

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO students (name, email, course, photo_url) "
                    "VALUES (%s, %s, %s, %s)",
                    (name, email, course, object_key),
                )
        finally:
            conn.close()
    except pymysql.MySQLError:
        logger.exception("Database insert failed")
        flash("We could not save your registration right now. Please try again shortly.", "error")
        return redirect(url_for("index"))

    photo_url = None
    try:
        photo_url = get_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": app.config["S3_BUCKET_NAME"], "Key": object_key},
            ExpiresIn=app.config["PRESIGNED_URL_EXPIRY_SECONDS"],
        )
    except (BotoCoreError, ClientError):
        logger.exception("Failed to generate pre-signed URL")

    return render_template("success.html", name=name, course=course, photo_url=photo_url)


@app.errorhandler(413)
def file_too_large(_e):
    flash("Photo is too large. Maximum upload size is 5 MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(500)
def internal_error(_e):
    logger.exception("Unhandled server error")
    return render_template("index.html", server_error=True), 500


if __name__ == "__main__":
    validate_config()
    # Development only. Production uses Gunicorn (see deploy/flaskapp.service).
    app.run(host="127.0.0.1", port=5000, debug=False)
elif not app.config.get("TESTING") and os.environ.get("SKIP_CONFIG_VALIDATION") != "1":
    validate_config()
