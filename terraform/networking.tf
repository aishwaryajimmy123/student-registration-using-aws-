# VPC + subnets + IGW + route tables.
#
# Cost note: this file intentionally does NOT create a NAT Gateway. Private
# subnets have no outbound internet route, which matches the spec's
# requirement ("Private subnets must not have a direct route to the Internet
# Gateway") and avoids NAT Gateway hourly + data-processing charges
# (~$0.045/hr + per-GB, i.e. real money if left running).
#
# Consequence: EC2 instances/services placed in the private subnets cannot
# reach the internet (e.g. for `dnf update`) unless you add a NAT Gateway or
# VPC endpoints yourself. RDS does not need outbound internet access, so this
# is not a problem for this project's architecture.

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = "${var.project_name}-vpc" })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${var.project_name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone_a
  map_public_ip_on_launch = true
  tags                    = merge(local.common_tags, { Name = "${var.project_name}-public-subnet" })
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_1_cidr
  availability_zone = var.availability_zone_a
  tags              = merge(local.common_tags, { Name = "${var.project_name}-private-subnet-1" })
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_2_cidr
  availability_zone = var.availability_zone_b
  tags              = merge(local.common_tags, { Name = "${var.project_name}-private-subnet-2" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${var.project_name}-public-rt" })
}

resource "aws_route" "public_internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id              = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Private route table has no route to the Internet Gateway (no NAT Gateway
# either), satisfying the "private subnets have no direct IGW route"
# requirement. It exists only so the subnets have an explicit table instead
# of implicitly using the VPC's main route table.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${var.project_name}-private-rt" })
}

resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private.id
}
