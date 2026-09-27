# Deployment Guide (Amazon Linux 2023, manual console approach)

Every command containing a value only you know is marked `<REPLACE_ME>`.
If you prefer Terraform for steps 1-4, see `../terraform/README.md` instead,
then skip to step 5.

## 1. VPC and Networking (Console)

1. VPC console → Create VPC → CIDR `10.0.0.0/16`, name `flask-app-vpc`.
2. Create subnets in that VPC:
   - `public-subnet`: `10.0.1.0/24`, AZ `<REPLACE_ME_az_a>`, enable
     auto-assign public IPv4.
   - `private-subnet-1`: `10.0.2.0/24`, AZ `<REPLACE_ME_az_a>`.
   - `private-subnet-2`: `10.0.3.0/24`, AZ `<REPLACE_ME_az_b>` (must differ
     from subnet 1's AZ — RDS subnet groups require 2+ AZs).
3. Create and attach an Internet Gateway to the VPC.
4. Create `public-rt` route table: add route `0.0.0.0/0 -> igw-...`,
   associate with `public-subnet`.
5. Create `private-rt` route table: leave only the default `local` route (no
   IGW route), associate with both private subnets.

## 2. Security Groups (Console)

1. Create `web-sg` in the VPC:
   - Inbound: SSH (22) from `<REPLACE_ME_your_ip>/32`; HTTP (80) from
     `0.0.0.0/0`.
   - Outbound: default (all traffic).
2. Create `db-sg` in the VPC:
   - Inbound: MySQL/Aurora (3306), source = `web-sg` (select the security
     group, not a CIDR).
   - Outbound: default.

## 3. IAM Role for EC2

1. IAM console → Policies → Create policy → JSON:
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
   Name it `flask-app-s3-access-policy`.
2. IAM console → Roles → Create role → Trusted entity: AWS service → EC2.
   Attach `flask-app-s3-access-policy`. Name it `flask-app-ec2-s3-role`.

## 4. S3 Bucket

1. S3 console → Create bucket → name `<REPLACE_ME_bucket_name>` (globally
   unique) → region `<REPLACE_ME_region>`.
2. Leave **Block all public access** checked (default, and required).
3. Enable default server-side encryption (SSE-S3/AES-256).

## 5. RDS MySQL

1. RDS console → Create database → Standard create → Engine: MySQL →
   Version: 8.0.x.
2. Templates: Free tier (for coursework) or Dev/Test.
3. DB instance identifier: `flask-app-mysql`.
4. Master username: `<REPLACE_ME_db_username>`. Master password:
   `<REPLACE_ME_db_password>` (use a strong, unique value — never reuse a
   real personal password).
5. Instance class: `db.t3.micro` (or Free Tier eligible equivalent).
6. Connectivity: VPC = your VPC. Create a new DB subnet group covering
   `private-subnet-1` and `private-subnet-2`. Public access: **No**. VPC
   security group: select existing → `db-sg` (remove default).
7. Initial database name: `studentdb`.
8. Create database. Wait for status "Available" before continuing (several
   minutes).

## 6. EC2 Instance

1. EC2 console → Launch instance → AMI: Amazon Linux 2023.
2. Instance type: `t3.micro` (or Free Tier eligible).
3. Key pair: create or select `<REPLACE_ME_key_pair_name>` (download the
   `.pem` and keep it secure; never commit it to git).
4. Network settings: VPC = your VPC, subnet = `public-subnet`, auto-assign
   public IP = enable. Security group: select existing → `web-sg`.
5. Advanced details → IAM instance profile: `flask-app-ec2-s3-role`.
6. Launch.

## 7. Connect and Prepare the EC2 Instance

```bash
chmod 400 <REPLACE_ME_key_pair_name>.pem
ssh -i <REPLACE_ME_key_pair_name>.pem ec2-user@<REPLACE_ME_ec2_public_ip>
```

```bash
# System update
sudo dnf update -y

# Python, pip, git, MySQL client
sudo dnf install -y python3.11 python3.11-pip git mariadb105

# Create a dedicated, unprivileged application user
sudo useradd --system --create-home --shell /usr/sbin/nologin flaskapp
```

## 8. Clone the Repository and Install Dependencies

```bash
sudo mkdir -p /opt/flaskapp
sudo chown ec2-user:ec2-user /opt/flaskapp
git clone <REPLACE_ME_your_repo_url> /opt/flaskapp
cd /opt/flaskapp

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

sudo chown -R flaskapp:flaskapp /opt/flaskapp
```

Allow the non-root `flaskapp` user's Python to bind to port 80 (a
privileged port) without running as root:

```bash
sudo setcap 'cap_net_bind_service=+ep' /opt/flaskapp/venv/bin/python3.11
```

## 9. Environment Configuration

```bash
sudo mkdir -p /etc/flaskapp
sudo tee /etc/flaskapp/flaskapp.env > /dev/null <<'EOF'
SECRET_KEY=<REPLACE_ME_random_secret>
DB_HOST=<REPLACE_ME_rds_endpoint>
DB_PORT=3306
DB_USER=<REPLACE_ME_db_username>
DB_PASSWORD=<REPLACE_ME_db_password>
DB_NAME=studentdb
S3_BUCKET_NAME=<REPLACE_ME_bucket_name>
AWS_REGION=<REPLACE_ME_region>
PRESIGNED_URL_EXPIRY_SECONDS=3600
EOF

sudo chown flaskapp:flaskapp /etc/flaskapp/flaskapp.env
sudo chmod 600 /etc/flaskapp/flaskapp.env
```

## 10. Create the Database Schema

From the EC2 instance (RDS is private and cannot be reached from your
laptop):

```bash
mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_db_username> -p < /opt/flaskapp/schema.sql
```

## 11. Test Database Connectivity

```bash
mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_db_username> -p \
  -e "USE studentdb; SHOW TABLES; DESCRIBE students;"
```

## 12. Test S3 Connectivity (using the IAM role, no keys)

```bash
sudo dnf install -y awscli
echo "connectivity test" > /tmp/s3test.txt
aws s3 cp /tmp/s3test.txt s3://<REPLACE_ME_bucket_name>/s3test.txt
aws s3 ls s3://<REPLACE_ME_bucket_name>/
aws s3 rm s3://<REPLACE_ME_bucket_name>/s3test.txt
rm /tmp/s3test.txt
```

If this succeeds without ever running `aws configure`, the IAM instance
role is working correctly.

## 13. Install and Start the systemd Service

```bash
sudo cp /opt/flaskapp/deploy/flaskapp.service /etc/systemd/system/flaskapp.service
sudo systemctl daemon-reload
sudo systemctl enable --now flaskapp
```

## 14. Verify Service Status and Logs

```bash
sudo systemctl status flaskapp
sudo journalctl -u flaskapp -f          # follow logs live, Ctrl+C to exit
sudo journalctl -u flaskapp -n 100      # last 100 log lines
```

## 15. Restart / Reload After Changes

```bash
# After pulling new code:
cd /opt/flaskapp
sudo -u flaskapp git pull
sudo -u flaskapp venv/bin/pip install -r requirements.txt
sudo systemctl restart flaskapp

# After changing /etc/flaskapp/flaskapp.env:
sudo systemctl restart flaskapp
```

## 16. Verify End-to-End

Open `http://<REPLACE_ME_ec2_public_ip>/` in a browser, submit the
registration form with a real image, and confirm:
- The success page shows a working (temporary) photo preview link.
- `SELECT * FROM studentdb.students;` on the EC2 instance shows the new row.
- `aws s3 ls s3://<REPLACE_ME_bucket_name>/student-photos/` shows the
  uploaded object.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `systemctl status flaskapp` shows `failed` | Missing/incorrect env vars, or port 80 permission | `journalctl -u flaskapp -n 50` for the exact error; re-check `setcap` step and `/etc/flaskapp/flaskapp.env` |
| Can't SSH to EC2 | Your IP changed since `web-sg` was created | Update the `web-sg` inbound rule for port 22 to your current IP |
| Can't load the site in a browser | `web-sg` missing port 80, or service not running | Check `web-sg` inbound rules; `sudo systemctl status flaskapp` |
| `pymysql.err.OperationalError: (2003, ...)` | `db-sg` doesn't allow EC2, or wrong `DB_HOST` | Confirm `db-sg` inbound rule references `web-sg`; confirm `DB_HOST` matches the RDS endpoint exactly |
| `botocore.exceptions.ClientError: AccessDenied` on S3 upload | IAM policy resource ARN doesn't match bucket, or role not attached | Confirm the instance profile is attached (EC2 console → instance → Security tab → IAM Role) and the policy's `Resource` matches the bucket ARN + `/*` |
| Registration succeeds but no photo preview | Pre-signed URL generation failed (logged server-side) or expired before viewing | Check `journalctl -u flaskapp`; increase `PRESIGNED_URL_EXPIRY_SECONDS` if needed |
| `pip install` fails building `cryptography` | Missing build tools on a minimal AMI | `sudo dnf groupinstall -y "Development Tools"` then retry |
