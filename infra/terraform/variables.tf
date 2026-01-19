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
# ECS task sizing (IMPORTANT BACKEND SKILL)
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

# -------------------------
# Application secrets / config
# -------------------------
variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  default     = "CHANGE_ME"
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  default     = "postgresql://user:password@localhost:5432/taskhub"
}

variable "redis_broker" {
  description = "Redis broker URL for Celery"
  type        = string
  default     = "redis://localhost:6379/0"
}
