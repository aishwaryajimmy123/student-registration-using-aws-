# EC2 instance in the public subnet, running the Flask/Gunicorn app.
# Uses the IAM instance profile from iam.tf — no access keys involved.
#
# This resource intentionally does NOT bootstrap the application via
# user_data. Follow docs/DEPLOYMENT.md to clone the repo, configure
# environment variables, and start the systemd service after the instance
# is created. Keeping deployment manual/scripted-but-explicit is easier for
# a student to understand and debug than a black-box user_data script.

resource "aws_instance" "web" {
  ami                         = var.ec2_ami_id
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.web_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_s3_profile.name
  key_name                    = var.key_pair_name
  associate_public_ip_address = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-web" })
}
