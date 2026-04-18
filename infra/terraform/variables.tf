# =============================================================================
# variables.tf — Input Variables
# =============================================================================

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

# -----------------------------------------------------------------------------
# Legacy aliases used in main.tf locals
# main.tf uses: local.name = "${var.project}-${var.env}"
# -----------------------------------------------------------------------------
variable "project" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "taskhub"
}

variable "env" {
  description = "Short environment name used in resource naming (alias for environment)"
  type        = string
  default     = "dev"
}

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "taskhub"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "taskhub"
}

variable "db_password" {
  description = "RDS PostgreSQL password — stored in Secrets Manager"
  type        = string
  sensitive   = true
  default     = "changeme"
}

variable "rds_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

# -----------------------------------------------------------------------------
# Secrets
# -----------------------------------------------------------------------------
variable "jwt_secret" {
  description = "JWT signing secret — stored in Secrets Manager"
  type        = string
  sensitive   = true
  default     = "changeme"
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = "alerts@example.com"
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch metrics"
  type        = string
  default     = ""
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for CloudWatch metrics"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------
variable "api_image" {
  description = "ECR image URI for the API container (include tag)"
  type        = string
  default     = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:latest"
}

variable "api_cpu" {
  description = "Fargate CPU units for the API task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Fargate memory (MB) for the API task"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired number of API task replicas"
  type        = number
  default     = 1
}

variable "worker_cpu" {
  description = "Fargate CPU units for the worker task"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Fargate memory (MB) for the worker task"
  type        = number
  default     = 512
}

variable "worker_desired_count" {
  description = "Desired number of worker task replicas"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# EventBridge
# -----------------------------------------------------------------------------
variable "event_bus_name" {
  description = "EventBridge event bus name"
  type        = string
  default     = "default"
}

# -----------------------------------------------------------------------------
# Autoscaling
# -----------------------------------------------------------------------------
variable "autoscaling_min_capacity" {
  description = "Minimum number of ECS tasks for autoscaling"
  type        = number
  default     = 1
}

variable "autoscaling_max_capacity" {
  description = "Maximum number of ECS tasks for autoscaling"
  type        = number
  default     = 4
}

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}
