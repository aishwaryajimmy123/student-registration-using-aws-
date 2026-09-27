# AWS Cloud Deployment Project — Secure Flask Web Application

A student registration web application demonstrating a secure, production-style
AWS deployment: Flask + Gunicorn on EC2, private RDS MySQL, S3 photo storage
accessed via an IAM instance role (no access keys), and network isolation
between public and private subnets.

## 1. Project Overview

Users visit a public web form, submit their name, email, course, and a photo.
The app uploads the photo to S3 using EC2's IAM role credentials, stores the
registration (including a reference to the photo) in a private RDS MySQL
database, and shows a success page with a time-limited pre-signed link to the
uploaded photo.

## 2. Architecture

```
                         Internet
                            |
                    Internet Gateway
                            |
                      Public Subnet
                     (10.0.1.0/24)
                            |
                 +----------------------+
                 |  EC2: Flask+Gunicorn |
                 |  IAM Instance Role   |----------------+
                 +----------------------+                |
                            |                              v
                Private Subnets (10.0.2.0/24,       +-----------+
                            10.0.3.0/24)             |  S3 Bucket|
                            |                        | (photos)  |
                     +-------------+                 +-----------+
                     | RDS MySQL   |
                     | (private,   |
                     |  db-sg)     |
                     +-------------+
```

- **web-sg** (on EC2): inbound 22 from admin IP only, 80 from the internet.
- **db-sg** (on RDS): inbound 3306 from `web-sg` only — never `0.0.0.0/0`.
- Private subnets have **no route** to the Internet Gateway.
- No NAT Gateway is used in the base project (cost avoidance); RDS does not
  need outbound internet access.

## 3. Technologies

- Python 3.11+, Flask 3, Gunicorn
- PyMySQL (MySQL 8.x driver)
- boto3 (AWS SDK) — credentials via EC2 IAM role only
- systemd (process supervision)
- Optional: Nginx (reverse proxy), Terraform (IaC)

## 4. AWS Components

| Component | Purpose |
|---|---|
| VPC (`10.0.0.0/16`) | Network isolation boundary |
| Public subnet (`10.0.1.0/24`) | Hosts the EC2 web server |
| Private subnets (`10.0.2.0/24`, `10.0.3.0/24`) | Hosts RDS (subnet group requires 2 AZs) |
| Internet Gateway | Public subnet internet access |
| Route tables | Public subnet → IGW; private subnets → no IGW route |
| EC2 (Amazon Linux 2023) | Runs Flask app via Gunicorn/systemd |
| RDS MySQL 8.x | Stores student registrations |
| S3 bucket | Stores uploaded photos |
| IAM role + instance profile | Grants EC2 scoped S3 access, no access keys |
| `web-sg` / `db-sg` | Network-level access control |

## 5. Directory Structure

```
flask/
├── app.py                  Flask application and routes
├── config.py                Environment-based configuration
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── schema.sql               MySQL schema (studentdb.students)
├── deploy/
│   ├── flaskapp.service     systemd unit (Gunicorn)
│   └── nginx.conf           optional reverse proxy config
├── templates/
│   ├── base.html
│   ├── index.html
│   └── success.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── tests/
│   └── test_app.py          Unit tests (AWS/DB mocked)
├── terraform/                optional IaC (see terraform/README.md)
└── docs/
    ├── ARCHITECTURE.md
    ├── SECURITY.md
    ├── DEPLOYMENT.md
    ├── TESTING.md
    └── SUBMISSION_CHECKLIST.md
```

## 6. Local Setup

```bash
git clone <REPLACE_ME_your_repo_url>
cd flask
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with local/test values. Real AWS credentials are never required
# locally if you only run the test suite (AWS calls are mocked).
pytest tests/ -v
```

To run the dev server locally against a real (or local) MySQL and AWS
account, fill in `.env` with real values and run:

```bash
python app.py
```

This uses Flask's built-in server for local development only — production
uses Gunicorn (see Deployment).

## 7. AWS Setup

Full manual console steps are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
An optional Terraform alternative is in [terraform/](terraform/README.md).

## 8. VPC Configuration

- VPC CIDR: `10.0.0.0/16`
- Public subnet: `10.0.1.0/24` (AZ a) — route to Internet Gateway
- Private subnet 1: `10.0.2.0/24` (AZ a)
- Private subnet 2: `10.0.3.0/24` (AZ b) — RDS subnet groups require 2+ AZs
- Private route table: local only, **no** route to the IGW

## 9. Security Groups

**web-sg** (EC2):
| Direction | Port | Source/Dest | Purpose |
|---|---|---|---|
| Inbound | 22 | Your IP `/32` | SSH admin access |
| Inbound | 80 | `0.0.0.0/0` | Public HTTP |
| Outbound | all | `0.0.0.0/0` | S3, package repos, RDS |

**db-sg** (RDS):
| Direction | Port | Source/Dest | Purpose |
|---|---|---|---|
| Inbound | 3306 | `web-sg` (by SG reference) | App → DB only |
| Outbound | all | `0.0.0.0/0` | default |

`0.0.0.0/0` is never used for database access.

## 10. IAM

EC2 instance role (`<REPLACE_ME_project>-ec2-s3-role`) with a single
least-privilege inline/managed policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::<REPLACE_ME_bucket_name>/*"
    }
  ]
}
```

No `Resource: "*"`. No IAM users or access keys are created for the
application; boto3 discovers credentials automatically via the EC2 instance
metadata service.

## 11. S3

- Bucket: `<REPLACE_ME_bucket_name>` (globally unique)
- Block Public Access: **fully enabled** (all four settings on)
- Server-side encryption: AES-256 (SSE-S3)
- Access pattern: EC2 role uploads objects via `PutObject`; the app then
  generates a **time-limited pre-signed URL** (`GetObject`, default 1 hour
  expiry) for the browser to display the photo. Objects are never made
  public.

**Behavior change vs. a "public bucket" starter approach**: the original
naive approach of returning a permanent public S3 URL is intentionally
replaced with pre-signed URLs, since Block Public Access is enabled and the
bucket policy grants no public read. This means photo links **expire**
(`PRESIGNED_URL_EXPIRY_SECONDS`, default 3600s) and must be regenerated per
view rather than being permanent, static links. The database stores the
S3 **object key**, not a URL, so a valid link can always be regenerated.

## 12. RDS

- Engine: MySQL 8.0
- Instance class: `db.t3.micro` (adjust as needed)
- Publicly Accessible: **No**
- Subnet group: both private subnets
- Security group: `db-sg` only
- Database: `studentdb`, table: `students` (see `schema.sql`)

## 13. EC2

- Amazon Linux 2023, in the public subnet
- IAM instance profile attached (no access keys)
- Security group: `web-sg`
- Runs the app via Gunicorn under systemd (`deploy/flaskapp.service`)

## 14. Environment Variables

See `.env.example`. Required at runtime:

```
SECRET_KEY=
DB_HOST=
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=studentdb
S3_BUCKET_NAME=
AWS_REGION=
PRESIGNED_URL_EXPIRY_SECONDS=3600
```

No AWS access keys are ever set — boto3 uses the EC2 IAM role automatically.
In production, these are supplied via `/etc/flaskapp/flaskapp.env` (mode
600), referenced by `EnvironmentFile=` in the systemd unit — never committed
to git.

## 15. Deployment

Full step-by-step commands: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

Summary:
1. Provision VPC/subnets/IGW/route tables/SGs.
2. Create S3 bucket (Block Public Access on) and IAM role/policy/instance
   profile.
3. Launch EC2 in the public subnet with the IAM role attached.
4. Create RDS MySQL in the private subnet group with `db-sg`.
5. On EC2: clone repo, create venv, install dependencies, configure
   `/etc/flaskapp/flaskapp.env`, run `schema.sql` against RDS, install and
   start the `flaskapp` systemd service.

## 16. Testing

```bash
pytest tests/ -v
```

Covers: `GET /`, missing-field validation, invalid email, disallowed file
type, a fully mocked successful registration (S3 + DB mocked), and graceful
handling of an S3 failure. No AWS account or live database is required. See
[docs/TESTING.md](docs/TESTING.md).

## 17. Security Validation

See the manual checklist in [docs/SECURITY.md](docs/SECURITY.md) and
[docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md).

## 18. Troubleshooting

See the troubleshooting section in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#troubleshooting).

## 19. Cleanup

To avoid ongoing AWS charges, delete resources in this order:

1. Terminate the EC2 instance.
2. Delete the RDS instance (skip final snapshot for a throwaway student
   project, or take one if you want to keep the data).
3. Empty and delete the S3 bucket.
4. Delete any NAT Gateway you created (none by default in this project) and
   release any associated Elastic IP.
5. Delete security groups, subnets, route tables, the Internet Gateway, and
   finally the VPC.
6. Delete the IAM role, instance profile, and policy if no longer needed.

If you used Terraform: `terraform destroy` (see `terraform/README.md`), then
verify manually in the console.

## 20. Project Limitations

- Single EC2 instance, no load balancer or auto scaling (out of scope per
  spec).
- No HTTPS/TLS termination configured (would require a domain + ACM
  certificate + ALB or Nginx + Let's Encrypt).
- No automated CI/CD pipeline.
- RDS has no automated backups configured by default in the Terraform
  example (`backup_retention_period = 0`) to minimize cost for a throwaway
  student environment — increase this for anything beyond coursework.
- Pre-signed URLs mean photo links expire; there is no caching/CDN layer.

## 21. Future Improvements

- Add Application Load Balancer + HTTPS (ACM certificate) in front of EC2.
- Move to an Auto Scaling Group across multiple AZs.
- Add CloudWatch alarms/logging and centralized log shipping.
- Add a CI pipeline that runs `pytest` and `terraform plan` on every PR.
- Consider RDS Proxy for connection pooling at higher scale.
- Add S3 lifecycle rules to expire old/unused photos.

## Architecture Diagram (ASCII)

```
 Internet
    |
    v
[Internet Gateway]
    |
    v
[Public Subnet 10.0.1.0/24]
    |
    v
[EC2: Gunicorn + Flask] --(IAM Role)--> [S3 Bucket: student-photos]
    |
    v
[Private Subnets 10.0.2.0/24, 10.0.3.0/24]
    |
    v
[RDS MySQL 8.x: studentdb.students]
```
