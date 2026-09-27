# S3 bucket for student photos. Block Public Access is fully enabled;
# objects are only ever accessed via time-limited pre-signed URLs generated
# by the application, or directly by the EC2 IAM role.

resource "aws_s3_bucket" "student_photos" {
  bucket = var.s3_bucket_name
  tags   = merge(local.common_tags, { Name = var.s3_bucket_name })
}

resource "aws_s3_bucket_public_access_block" "student_photos" {
  bucket = aws_s3_bucket.student_photos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "student_photos" {
  bucket = aws_s3_bucket.student_photos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "student_photos" {
  bucket = aws_s3_bucket.student_photos.id
  versioning_configuration {
    status = "Disabled"
  }
}
