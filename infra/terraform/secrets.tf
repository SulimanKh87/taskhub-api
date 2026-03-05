# infra/terraform/secrets.tf
# =============================================================================
# AWS Secrets Manager for Production Secrets
# =============================================================================

# -----------------------------------------------------------------------------
# Database Password
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db_password" {
  name        = "${local.name}-db-password"
  description = "RDS PostgreSQL master password"

  tags = {
    Name = "${local.name}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password
}

# -----------------------------------------------------------------------------
# JWT Secret
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "${local.name}-jwt-secret"
  description = "JWT signing secret for authentication"

  tags = {
    Name = "${local.name}-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret
}

# -----------------------------------------------------------------------------
# Outputs for ECS task definitions
# -----------------------------------------------------------------------------
output "db_password_secret_arn" {
  value       = aws_secretsmanager_secret.db_password.arn
  description = "ARN of DB password secret"
}

output "jwt_secret_arn" {
  value       = aws_secretsmanager_secret.jwt_secret.arn
  description = "ARN of JWT secret"
}