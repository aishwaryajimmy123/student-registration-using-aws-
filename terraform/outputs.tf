output "ec2_public_ip" {
  value = aws_instance.web.public_ip
}

output "ec2_instance_id" {
  value = aws_instance.web.id
}

output "rds_endpoint" {
  value = aws_db_instance.studentdb.address
}

output "s3_bucket_name" {
  value = aws_s3_bucket.student_photos.bucket
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "web_sg_id" {
  value = aws_security_group.web_sg.id
}

output "db_sg_id" {
  value = aws_security_group.db_sg.id
}

output "ec2_iam_role_name" {
  value = aws_iam_role.ec2_s3_role.name
}
