# Architecture

## Request flow

1. Browser requests `GET /` → EC2 (Gunicorn → Flask) renders `templates/index.html`.
2. Browser submits `POST /register` with `multipart/form-data` (name, email,
   course, photo).
3. `app.py::register()`:
   - Validates all fields server-side (`validate_registration_form`).
   - Builds a random UUID-based S3 object key (`build_safe_object_key`) —
     the original filename is never used to construct a path.
   - Calls `s3.upload_fileobj(...)` using a boto3 client whose credentials
     come from the EC2 instance's attached IAM role (instance metadata
     service), never from hardcoded keys.
   - Opens a PyMySQL connection (host/user/password/db from environment
     variables only) and inserts a row into `students` using a parameterized
     query.
   - Generates a pre-signed `GetObject` URL (default 1-hour expiry) for the
     just-uploaded object.
   - Renders `templates/success.html` with the pre-signed URL.
4. On any S3 or database failure, the user sees a generic flash message; the
   real exception is logged server-side only (`logger.exception(...)`), never
   returned in the HTTP response.

## Network path

```
Internet --80--> IGW --> Public Subnet (10.0.1.0/24) --> EC2 (web-sg)
                                                              |
                                                    3306 (db-sg only)
                                                              v
                                    Private Subnets (10.0.2.0/24, 10.0.3.0/24)
                                                              |
                                                          RDS MySQL
```

EC2 also talks to S3 over the public AWS API endpoint (`s3.<region>.amazonaws.com`)
via its outbound internet route in the public subnet — this does not require
S3 to be reachable from the private subnets, since S3 calls originate from
EC2 in the public subnet, not from RDS.

## Why no NAT Gateway

The private subnets host only RDS, which does not need outbound internet
access to serve queries from EC2. Adding a NAT Gateway here would only add
cost (hourly + per-GB charges) without functional benefit for this
architecture, so it is deliberately omitted. If you later add resources to
the private subnets that need outbound internet (e.g. a background worker
pulling from an external API), you would need to add a NAT Gateway and a
route from the private route table to it at that point.

## Why pre-signed URLs instead of public S3 objects

The spec's more secure option — keeping Block Public Access enabled and
using the EC2 IAM role plus pre-signed URLs — was chosen over making the
bucket or individual objects public. Consequences documented in the main
README (section 11): the database stores the object key rather than a full
URL, and displayed photo links expire after `PRESIGNED_URL_EXPIRY_SECONDS`.
