# web-sg: attached to the EC2 instance.
#   - Inbound: SSH (22) from your IP only, HTTP (80) from anywhere.
#   - Outbound: all (needed to reach S3 endpoints, RDS, package repos).
resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Security group for the public-facing Flask/Gunicorn EC2 instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH from admin IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "web-sg" })
}

# db-sg: attached to the RDS instance.
#   - Inbound: MySQL (3306) from web-sg ONLY — never 0.0.0.0/0.
#   - No outbound rules needed beyond default (RDS does not initiate
#     outbound connections for this app).
resource "aws_security_group" "db_sg" {
  name        = "db-sg"
  description = "Security group for the private RDS MySQL instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from web-sg only"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "db-sg" })
}
