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
# Secrets (sensitive — never put real values in this file)
# Supply via terraform.tfvars or environment variables:
#   export TF_VAR_db_password="..."
#   export TF_VAR_jwt_secret="..."
# -----------------------------------------------------------------------------
variable "db_password" {
  description = "RDS PostgreSQL password — stored in Secrets Manager"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret — stored in Secrets Manager"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------
variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = "alerts@example.com"
}

# -----------------------------------------------------------------------------
# Networking (populated from main.tf outputs or remote state)
# -----------------------------------------------------------------------------
variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "api_security_group_id" {
  description = "Security group ID for API ECS tasks"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN for the API service"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch metrics"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for CloudWatch metrics"
  type        = string
}

variable "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  type        = string
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
