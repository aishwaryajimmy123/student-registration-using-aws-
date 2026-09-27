# RDS MySQL 8.x, private, in a DB subnet group spanning both private
# subnets. Publicly inaccessible; reachable only from web-sg on 3306.

resource "aws_db_subnet_group" "studentdb" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  tags       = local.common_tags
}

resource "aws_db_instance" "studentdb" {
  identifier                  = "${var.project_name}-mysql"
  engine                      = "mysql"
  engine_version              = "8.0"
  instance_class              = var.db_instance_class
  allocated_storage           = 20
  storage_type                = "gp3"
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  db_subnet_group_name        = aws_db_subnet_group.studentdb.name
  vpc_security_group_ids      = [aws_security_group.db_sg.id]
  publicly_accessible         = false
  multi_az                    = false
  skip_final_snapshot         = true
  deletion_protection         = false
  backup_retention_period     = 0
  auto_minor_version_upgrade  = true

  tags = local.common_tags
}
