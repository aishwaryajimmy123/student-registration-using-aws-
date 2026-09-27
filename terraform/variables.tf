variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used to tag/prefix resources."
  type        = string
  default     = "flask-student-app"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "private_subnet_1_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

variable "private_subnet_2_cidr" {
  type    = string
  default = "10.0.3.0/24"
}

variable "availability_zone_a" {
  description = "AZ for the public subnet and private subnet 1."
  type        = string
  default     = "us-east-1a"
}

variable "availability_zone_b" {
  description = "AZ for private subnet 2 (RDS requires 2+ AZs for a subnet group)."
  type        = string
  default     = "us-east-1b"
}

variable "my_ip_cidr" {
  description = "Your public IP in CIDR form, e.g. 203.0.113.5/32. Used to restrict SSH. REPLACE_ME."
  type        = string
}

variable "key_pair_name" {
  description = "Existing EC2 key pair name for SSH access. Create manually in the console. REPLACE_ME."
  type        = string
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "ec2_ami_id" {
  description = "Amazon Linux 2023 AMI ID for the chosen region. REPLACE_ME (varies per region)."
  type        = string
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "studentdb"
}

variable "db_username" {
  description = "Master username for RDS. REPLACE_ME."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Master password for RDS. REPLACE_ME. Never commit a real value or a .tfvars file containing it."
  type        = string
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "Globally-unique S3 bucket name for student photos. REPLACE_ME."
  type        = string
}
