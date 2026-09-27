# Testing

## Automated unit tests

`tests/test_app.py` covers:

- `GET /` returns 200 and renders the registration form fields.
- `POST /register` with no data returns all four required-field errors.
- `POST /register` with an invalid email returns the email validation error.
- `POST /register` with a disallowed file type (`.exe`) is rejected.
- `POST /register` with valid data, S3 and DB mocked, succeeds and:
  - calls `s3.upload_fileobj` exactly once,
  - inserts exactly one row via a parameterized `INSERT INTO students` query
    with the correct values in the correct order,
  - renders the success page with the submitted name.
- `POST /register` where S3 raises `ClientError` shows a graceful error
  message instead of crashing or leaking the exception.

No AWS account, no real S3 bucket, and no real MySQL/RDS instance are
required to run these tests — `boto3` and `pymysql` calls are mocked with
`pytest-mock`.

Run them with:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/ -v
```

Expected output: all tests pass (6 passed, as of this writing).

## Manual functional testing (requires a deployed environment)

1. Open `http://<ec2-public-ip>/` — confirm the form renders.
2. Submit with an empty form — confirm inline validation (browser) prevents
   submission, or (if bypassed) the server returns the same field errors as
   the automated tests.
3. Submit with a valid name/email/course and a real `.jpg`/`.png` file under
   5 MB — confirm redirect to the success page with a working photo preview.
4. Submit with a `.txt` or `.exe` file renamed to `.jpg` — confirm the
   MIME-type check rejects it (Flask/Werkzeug inspects the browser-supplied
   `Content-Type`, which is a reasonable but not bulletproof check for a
   student project; see Security Trade-offs in `docs/SECURITY.md`).
5. Submit a file larger than 5 MB — confirm the "too large" error is shown,
   not a raw 413 response.
6. Verify persistence: on the EC2 instance,
   ```bash
   mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_db_username> -p \
     -e "SELECT id, name, email, course, photo_url FROM studentdb.students ORDER BY id DESC LIMIT 5;"
   ```
7. Verify the S3 object exists:
   ```bash
   aws s3 ls s3://<REPLACE_ME_bucket_name>/student-photos/
   ```

## What is intentionally not tested

- Real AWS integration (S3/RDS) is not covered by automated tests, since the
  spec requires tests to run without an AWS account. Manual testing (above)
  covers this instead.
- Load/performance testing is out of scope for this project.
