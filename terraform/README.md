# Terraform (Optional)

This Terraform configuration is an **optional** alternative to building the
architecture manually in the AWS Console (which is what the project spec
primarily describes and what `docs/DEPLOYMENT.md` walks through). Use
whichever approach your assignment requires; the two produce the same
architecture.

## What this creates automatically

- VPC (`10.0.0.0/16`), 1 public + 2 private subnets, Internet Gateway,
  public/private route tables (`networking.tf`)
- `web-sg` and `db-sg` security groups (`security_groups.tf`)
- IAM role + least-privilege policy + instance profile for EC2 (`iam.tf`)
- S3 bucket with Block Public Access enabled (`s3.tf`)
- RDS MySQL 8.0 instance, private, in a DB subnet group (`rds.tf`)
- EC2 instance in the public subnet with the IAM instance profile attached
  (`ec2.tf`)

## What you must still do manually

1. Create an EC2 key pair in the console (or `aws ec2 create-key-pair`) and
   pass its name as `key_pair_name`.
2. Look up the current Amazon Linux 2023 AMI ID for your region and pass it
   as `ec2_ami_id`.
3. Deploy the application code onto the EC2 instance and start the systemd
   service — see `../docs/DEPLOYMENT.md`. This Terraform config does not run
   any application bootstrapping.
4. Create the `students` table (`../schema.sql`) against the RDS instance
   from the EC2 instance (RDS is private and unreachable from your laptop).

## Cost warnings — read before running `apply`

All of these are **billable**, even at small scale:

- **RDS** (`db.t3.micro` by default): billed per hour whether idle or not,
  plus storage. Not covered by the AWS Free Tier after 12 months, and even
  within Free Tier limits are capped hours/month.
- **EC2** (`t3.micro` by default): billed per hour while running.
- **NAT Gateway**: **this configuration deliberately does NOT create one**
  (see the comment in `networking.tf`) specifically to avoid its hourly +
  per-GB charges. Do not add one unless you understand the cost impact —
  a NAT Gateway left running is one of the most common sources of surprise
  AWS bills.
- **Elastic IP**: not created here; the EC2 instance uses its default public
  IP, which is free while the instance is running but can incur a small
  charge if allocated as an Elastic IP and left unattached.
- **S3**: storage + request costs are minor for a student project but not
  zero.

Never assume any of the above is free — verify current pricing for your
region before applying.

## Usage

```bash
cd terraform
terraform init
terraform plan \
  -var="my_ip_cidr=<REPLACE_ME>/32" \
  -var="key_pair_name=<REPLACE_ME>" \
  -var="ec2_ami_id=<REPLACE_ME>" \
  -var="db_username=<REPLACE_ME>" \
  -var="db_password=<REPLACE_ME>" \
  -var="s3_bucket_name=<REPLACE_ME>"
terraform apply <same -var flags as above>
```

Never put `db_password` or other secrets in a committed `.tfvars` file.
Either pass them with `-var` on the command line (as above), or use a
`.tfvars` file that is listed in `.gitignore` (it already is).

## Cleanup

```bash
terraform destroy <same -var flags as above>
```

Then verify in the console that the VPC, RDS instance, EC2 instance, S3
bucket, and IAM role were actually removed — `terraform destroy` can fail
partway through (e.g. a non-empty S3 bucket) and leave billable resources
behind. Empty the S3 bucket manually first if destroy reports it is not empty.
