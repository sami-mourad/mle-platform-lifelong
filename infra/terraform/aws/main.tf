provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = local.name }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = local.name }
}

resource "aws_subnet" "public" {
  for_each                = toset(local.azs)
  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.value
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, index(local.azs, each.value))
  map_public_ip_on_launch = true
  tags                    = { Name = "${local.name}-public-${each.value}" }
}

resource "aws_subnet" "private" {
  for_each          = toset(local.azs)
  vpc_id            = aws_vpc.this.id
  availability_zone = each.value
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, index(local.azs, each.value) + 8)
  tags              = { Name = "${local.name}-private-${each.value}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
}

resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_s3_bucket" "artifacts" {
  bucket_prefix = "${local.name}-artifacts-"
  force_destroy = var.environment != "prod"
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_db_subnet_group" "this" {
  name       = local.name
  subnet_ids = [for subnet in aws_subnet.private : subnet.id]
}

resource "aws_security_group" "database" {
  name   = "${local.name}-database"
  vpc_id = aws_vpc.this.id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "metadata" {
  identifier                   = "${local.name}-metadata"
  engine                       = "postgres"
  engine_version               = "17"
  instance_class               = "db.t4g.micro"
  allocated_storage            = 20
  max_allocated_storage        = 100
  storage_encrypted            = true
  username                     = var.database_username
  password                     = var.database_password
  db_name                      = "platform"
  db_subnet_group_name         = aws_db_subnet_group.this.name
  vpc_security_group_ids       = [aws_security_group.database.id]
  publicly_accessible          = false
  backup_retention_period      = var.environment == "prod" ? 14 : 1
  deletion_protection          = var.environment == "prod"
  skip_final_snapshot          = var.environment != "prod"
  performance_insights_enabled = true
}

resource "aws_elasticache_subnet_group" "this" {
  name       = local.name
  subnet_ids = [for subnet in aws_subnet.private : subnet.id]
}

resource "aws_security_group" "redis" {
  name   = "${local.name}-redis"
  vpc_id = aws_vpc.this.id
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_replication_group" "online_state" {
  replication_group_id       = "${local.name}-online-state"
  description                = "Online/cache state for ${local.name}"
  node_type                  = "cache.t4g.micro"
  num_cache_clusters         = var.environment == "prod" ? 2 : 1
  engine                     = "redis"
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  automatic_failover_enabled = var.environment == "prod"
  subnet_group_name          = aws_elasticache_subnet_group.this.name
  security_group_ids         = [aws_security_group.redis.id]
}

resource "aws_ecr_repository" "services" {
  for_each = toset(["mlflow", "dagster", "api"])
  name     = "${local.name}/${each.value}"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
}

resource "aws_ecs_cluster" "this" {
  name = local.name
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "services" {
  for_each          = toset(["mlflow", "dagster", "api"])
  name              = "/ecs/${local.name}/${each.value}"
  retention_in_days = var.environment == "prod" ? 90 : 14
}
