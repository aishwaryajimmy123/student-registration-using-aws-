# Submission Checklist

For each item, capture a screenshot showing exactly the described content.

## 1. Architecture diagram
- [ ] The ASCII diagram from `README.md` (or a drawn equivalent) showing
      Internet → IGW → Public Subnet → EC2 → Private Subnets → RDS, and
      EC2 → IAM Role → S3.

## 2. VPC / subnet evidence
- [ ] VPC console: VPC detail page showing CIDR `10.0.0.0/16`.
- [ ] Subnets list showing all three subnets with their CIDRs and AZs.
- [ ] Route tables: public route table showing the `0.0.0.0/0 -> igw-...`
      route.
- [ ] Route tables: private route table showing **no** IGW route.

## 3. Security group evidence
- [ ] `web-sg` inbound rules: 22 from your IP `/32`, 80 from `0.0.0.0/0`.
- [ ] `db-sg` inbound rules: 3306 with source = `web-sg` (shown as a
      security-group reference, not a CIDR).

## 4. IAM role/policy evidence
- [ ] IAM role detail page showing the trust relationship (EC2 service) and
      the attached policy name.
- [ ] The policy's JSON showing `s3:PutObject`/`s3:GetObject` scoped to
      `arn:aws:s3:::<bucket>/*` (no `"Resource": "*"`).
- [ ] EC2 instance detail page → Security tab showing the IAM role attached.

## 5. RDS private-access evidence
- [ ] RDS instance detail page showing "Publicly Accessible: No".
- [ ] Terminal showing a failed connection attempt from your laptop to the
      RDS endpoint (e.g. `mysql -h ... ` timing out).
- [ ] Terminal (SSH'd into EC2) showing a successful `mysql -h ... -e "SELECT 1;"`.

## 6. EC2 IAM-role evidence
- [ ] Terminal on EC2 running `aws s3 cp` / `aws s3 ls` successfully with
      no `aws configure` credentials ever set on the instance.

## 7. Working registration form
- [ ] Screenshot of the rendered form at `http://<ec2-ip>/`.

## 8. Successful submission
- [ ] Screenshot of the success page after submitting real data + a photo,
      showing the working photo preview.

## 9. MySQL inserted row
- [ ] Terminal output of
      `SELECT * FROM studentdb.students ORDER BY id DESC LIMIT 1;`
      showing the row that matches the submission above.

## 10. S3 uploaded object
- [ ] `aws s3 ls s3://<bucket>/student-photos/` (or S3 console listing)
      showing the uploaded object key.

## 11. GitHub repository
- [ ] Link to the public/private GitHub repo containing this project.
- [ ] Confirm `.env`, `*.pem`, and `terraform.tfstate`/`*.tfvars` are absent
      from the repo (check the file list, not just `.gitignore`).

## 12. Security checklist
- [ ] Completed copy of the 10-point checklist in `docs/SECURITY.md`.

## 13. Security trade-off write-up
- [ ] Short (~1 page) write-up covering: why pre-signed URLs were chosen
      over public S3 objects, why no NAT Gateway was used, and one thing
      you would improve with more time/budget (see README section 21,
      Future Improvements, for ideas — write this in your own words).
