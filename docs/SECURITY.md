# Security

## Implemented controls

| Area | Control | Where |
|---|---|---|
| Credentials | No AWS access keys anywhere in code or config | `app.py` uses `boto3.client("s3")` with no explicit credentials |
| Credentials | DB credentials only from environment variables | `config.py` |
| Secrets | `.env`, keys, and Terraform state/vars excluded from git | `.gitignore` |
| SQL | Parameterized queries only | `app.py::register()` |
| Uploads | Filename never trusted; UUID-based key generated server-side | `build_safe_object_key()` |
| Uploads | Extension + MIME type allow-list, 5 MB size cap | `config.py`, `app.py::allowed_file()`, `MAX_CONTENT_LENGTH` |
| Error handling | No stack traces, DB passwords, or AWS credentials returned to the client | `logger.exception(...)` + generic flash messages, `@app.errorhandler(500)` |
| Network | RDS not publicly accessible | RDS console setting / `publicly_accessible = false` in Terraform |
| Network | `db-sg` allows 3306 from `web-sg` only | `security_groups.tf` |
| Network | SSH restricted to admin IP | `web-sg` inbound rule |
| Network | Private subnets have no IGW route | `networking.tf` |
| IAM | Least privilege: `s3:PutObject`/`s3:GetObject` scoped to one bucket | `iam.tf` |
| S3 | Block Public Access fully enabled | `s3.tf` |
| S3 | Time-limited pre-signed URLs instead of public objects | `app.py::register()` |
| Process | Runs as a dedicated non-root `flaskapp` system user | `deploy/flaskapp.service` |

## Manual AWS validation checklist

Run these checks after deployment and capture evidence per
`docs/SUBMISSION_CHECKLIST.md`.

1. **RDS Publicly Accessible = No** — RDS console → your instance →
   Connectivity & security → confirm "No".
2. **RDS unreachable from your laptop** —
   ```bash
   mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_user> -p
   ```
   from your local machine should time out / fail to connect.
3. **EC2 can reach RDS** — from an SSH session on the EC2 instance:
   ```bash
   mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_user> -p -e "SELECT 1;"
   ```
   should succeed.
4. **`db-sg` allows 3306 only from `web-sg`** — EC2 console → Security
   Groups → `db-sg` → Inbound rules → confirm the only 3306 rule's source is
   `web-sg` (by security group ID, not a CIDR).
5. **SSH restricted to your IP** — `web-sg` → Inbound rules → confirm port
   22's source is `<your-ip>/32`, not `0.0.0.0/0`.
6. **EC2 can upload to S3 using its IAM role** —
   ```bash
   echo "test" > /tmp/test.txt
   aws s3 cp /tmp/test.txt s3://<REPLACE_ME_bucket_name>/test.txt
   aws s3 rm s3://<REPLACE_ME_bucket_name>/test.txt
   ```
   run on the EC2 instance with **no** `aws configure` credentials set —
   success confirms the instance role is working.
7. **No AWS keys in source code** —
   ```bash
   grep -rEi "AKIA[0-9A-Z]{16}" .
   ```
   should return nothing.
8. **No passwords in git history** —
   ```bash
   git log -p | grep -i "password" 
   ```
   review any hits manually; should find only variable names/placeholders,
   never real values.
9. **S3 bucket cannot be listed publicly** — in an incognito browser (not
   logged into AWS), try:
   `https://<REPLACE_ME_bucket_name>.s3.amazonaws.com/` — should return
   `AccessDenied`, not a file listing.
10. **Private subnet has no IGW route** — VPC console → Route Tables →
    the private route table → Routes tab → confirm there is no
    `0.0.0.0/0 -> igw-...` entry.

## Known trade-offs

- No TLS/HTTPS is configured for the base project (HTTP only on port 80).
  For coursework this is accepted, but a real deployment should add HTTPS
  via an ALB + ACM certificate or Nginx + Let's Encrypt.
- Pre-signed URLs are time-limited (`PRESIGNED_URL_EXPIRY_SECONDS`), which
  is a security benefit but means links are not permanent — the app must
  regenerate them on demand.
- The `flaskapp` systemd service still needs `EnvironmentFile` permissions
  managed carefully (mode 600, correct owner) since it contains the DB
  password in plaintext on disk — this is a standard trade-off for
  environment-variable-based configuration versus a secrets manager
  (AWS Secrets Manager / SSM Parameter Store would be a stronger but more
  complex alternative, listed under Future Improvements).
