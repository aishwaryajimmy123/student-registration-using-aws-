-- Run against the RDS MySQL 8.x instance from the EC2 web server
-- (RDS is private; this cannot be run from your laptop directly).
--
--   mysql -h <REPLACE_ME_rds_endpoint> -u <REPLACE_ME_db_username> -p < schema.sql

CREATE DATABASE IF NOT EXISTS studentdb
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE studentdb;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    course VARCHAR(100),
    photo_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
