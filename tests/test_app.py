"""
Unit tests for the Flask student registration app.

No real AWS account or database is required: boto3 (S3) and PyMySQL (RDS)
calls are mocked. Required environment variables are set before import so
config.validate_config() does not raise.
"""

import io
import os
import sys

import pytest

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME", "studentdb")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("SECRET_KEY", "test-secret")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as flask_app_module  # noqa: E402


@pytest.fixture
def client():
    flask_app_module.app.config["TESTING"] = True
    with flask_app_module.app.test_client() as client:
        yield client


def test_get_index_returns_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration" in response.data
    assert b"name=\"name\"" in response.data
    assert b"name=\"email\"" in response.data
    assert b"name=\"course\"" in response.data
    assert b"name=\"photo\"" in response.data


def test_register_missing_all_fields_redirects_with_errors(client):
    response = client.post("/register", data={}, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    body = response.data.decode()
    assert "Name is required." in body
    assert "Email is required." in body
    assert "Course is required." in body
    assert "A photo is required." in body


def test_register_invalid_email(client):
    data = {
        "name": "Ada Lovelace",
        "email": "not-an-email",
        "course": "Computer Science",
        "photo": (io.BytesIO(b"fake-image-bytes"), "photo.png", "image/png"),
    }
    response = client.post(
        "/register", data=data, content_type="multipart/form-data", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"A valid email address is required." in response.data


def test_register_disallowed_file_type(client):
    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "course": "Computer Science",
        "photo": (io.BytesIO(b"not-really-an-exe"), "malware.exe", "application/octet-stream"),
    }
    response = client.post(
        "/register", data=data, content_type="multipart/form-data", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Photo must be a PNG, JPG, or GIF image." in response.data


def test_successful_registration_mocks_s3_and_db(client, mocker):
    mock_s3 = mocker.MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://example-bucket.s3.amazonaws.com/signed-url"
    mocker.patch.object(flask_app_module, "get_s3_client", return_value=mock_s3)

    mock_cursor = mocker.MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch.object(flask_app_module, "get_db_connection", return_value=mock_conn)

    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "course": "Computer Science",
        "photo": (io.BytesIO(b"fake-image-bytes"), "photo.png", "image/png"),
    }
    response = client.post(
        "/register", data=data, content_type="multipart/form-data", follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Registration Successful" in response.data
    assert b"Ada Lovelace" in response.data

    mock_s3.upload_fileobj.assert_called_once()
    mock_cursor.execute.assert_called_once()
    executed_sql = mock_cursor.execute.call_args[0][0]
    executed_params = mock_cursor.execute.call_args[0][1]
    assert "INSERT INTO students" in executed_sql
    assert executed_params[0] == "Ada Lovelace"
    assert executed_params[1] == "ada@example.com"
    assert executed_params[2] == "Computer Science"


def test_registration_handles_s3_failure_gracefully(client, mocker):
    from botocore.exceptions import ClientError

    mock_s3 = mocker.MagicMock()
    mock_s3.upload_fileobj.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "denied"}}, "PutObject"
    )
    mocker.patch.object(flask_app_module, "get_s3_client", return_value=mock_s3)

    data = {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "course": "Computer Science",
        "photo": (io.BytesIO(b"fake-image-bytes"), "photo.png", "image/png"),
    }
    response = client.post(
        "/register", data=data, content_type="multipart/form-data", follow_redirects=True
    )

    assert response.status_code == 200
    assert b"could not upload your photo" in response.data
