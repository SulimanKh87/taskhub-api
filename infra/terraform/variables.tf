# variables.tf
# -------------------------
# Project / environment
# -------------------------
variable "project" {
  description = "Project name (used as prefix for all resources)"
  type        = string
  default     = "taskhub"
}

variable "env" {
  description = "Environment name (dev / staging / prod)"
  type        = string
  default     = "dev"
}

# -------------------------
# AWS settings
# -------------------------
variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "eu-central-1"
}

# -------------------------
# Container images
# -------------------------
variable "api_image" {
  description = "Docker image for the FastAPI service (ECR image URI)"
  type        = string
  default     = "example/taskhub-api:latest"
}

variable "worker_image" {
  description = "Docker image for the Celery worker (ECR image URI)"
  type        = string
  default     = "example/taskhub-worker:latest"
}

# -------------------------
# ECS task sizing
# -------------------------
variable "api_cpu" {
  description = "CPU units for the API ECS task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Memory (MB) for the API ECS task"
  type        = number
  default     = 512
}

variable "worker_cpu" {
  description = "CPU units for the Celery worker ECS task"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Memory (MB) for the Celery worker ECS task"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired tasks for API service"
  type        = number
  default     = 1
}

variable "worker_desired_count" {
  description = "Desired tasks for Celery worker service"
  type        = number
  default     = 1
}

# -------------------------
# App config / secrets (for learning: env vars in task definition)
# Later: move secrets to SSM/Secrets Manager
# -------------------------
variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  default     = "CHANGE_ME"
}

# -------------------------
# RDS (Postgres)
# -------------------------
variable "db_name" {
  description = "Database name for Postgres"
  type        = string
  default     = "taskhub"
}

variable "db_username" {
  description = "Master username for Postgres"
  type        = string
  default     = "taskhub"
}

variable "db_password" {
  description = "Master password for Postgres (do NOT commit real secrets)"
  type        = string
  sensitive   = true
  default     = "taskhub_pass_CHANGE_ME"
}

# -------------------------
# Secrets Manager (Optional - Future Migration)
# -------------------------
variable "db_password_secret_arn" {
  description = "ARN of DB password in AWS Secrets Manager (optional). When set, overrides db_password variable."
  type        = string
  default     = null
}

variable "jwt_secret_arn" {
  description = "ARN of JWT secret in AWS Secrets Manager (optional). When set, overrides jwt_secret variable."
  type        = string
  default     = null
}

# -------------------------
# RDS Configuration
# -------------------------
variable "rds_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage (GB)"
  type        = number
  default     = 20
}

# -------------------------
# ElastiCache (Redis)
# -------------------------
variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t4g.micro"
}

# -------------------------
# Logs
# -------------------------
variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
  default     = 7
}
