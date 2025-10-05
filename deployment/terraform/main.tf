# SAR Drone System - Production Infrastructure
# Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
  
  backend "s3" {
    bucket = "sar-drone-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "SAR-Drone-System"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "sar-drone-cluster"
}

variable "node_group_instance_types" {
  description = "Instance types for EKS node group"
  type        = list(string)
  default     = ["t3.large", "t3.xlarge"]
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
  
  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }
  
  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = "1.28"
  
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true
  
  # EKS Managed Node Groups
  eks_managed_node_groups = {
    main = {
      name = "main"
      
      instance_types = var.node_group_instance_types
      
      min_size     = 2
      max_size     = 10
      desired_size = 3
      
      capacity_type = "ON_DEMAND"
      
      labels = {
        role = "main"
      }
    }
    
    compute = {
      name = "compute"
      
      instance_types = ["c5.xlarge", "c5.2xlarge"]
      
      min_size     = 1
      max_size     = 5
      desired_size = 2
      
      capacity_type = "ON_DEMAND"
      
      labels = {
        role = "compute"
      }
      
      taints = {
        compute = {
          key    = "compute"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
  
  # aws-auth configmap
  manage_aws_auth_configmap = true
  
  aws_auth_roles = [
    {
      rolearn  = aws_iam_role.cluster_admin.arn
      username = "cluster-admin"
      groups   = ["system:masters"]
    }
  ]
  
  tags = {
    Environment = var.environment
  }
}

# RDS PostgreSQL
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "sar-drone-postgres"
  
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r5.large"
  
  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_encrypted     = true
  
  db_name  = "sar_drone"
  username = "sar_admin"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = true
  
  tags = {
    Name = "SAR Drone PostgreSQL"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "sar-drone-redis"
  description                = "SAR Drone Redis Cluster"
  
  node_type                  = "cache.r5.large"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 2
  
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  snapshot_retention_limit = 5
  snapshot_window         = "03:00-05:00"
  
  tags = {
    Name = "SAR Drone Redis"
  }
}

# S3 Bucket for ML Models and Data
resource "aws_s3_bucket" "sar_data" {
  bucket = "sar-drone-data-${random_string.bucket_suffix.result}"
  
  tags = {
    Name = "SAR Drone Data Storage"
  }
}

resource "aws_s3_bucket_versioning" "sar_data" {
  bucket = aws_s3_bucket.sar_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sar_data" {
  bucket = aws_s3_bucket.sar_data.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "sar-drone-rds"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "SAR Drone RDS Security Group"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "sar-drone-redis"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "SAR Drone Redis Security Group"
  }
}

# IAM Roles
resource "aws_iam_role" "cluster_admin" {
  name = "SAR-Drone-Cluster-Admin"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
      }
    ]
  })
}

# Outputs
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_instance_endpoint
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "s3_bucket" {
  description = "S3 bucket for data storage"
  value       = aws_s3_bucket.sar_data.bucket
}
