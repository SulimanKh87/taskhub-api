# infra/terraform/secrets.tf
# =============================================================================
# secrets.tf — AWS Secrets Manager
#
# WHY SECRETS MANAGER INSTEAD OF ENV VARS IN TASK DEFINITION?
#   - Plaintext secrets in ECS task definitions appear in:
#     * AWS Console (visible to anyone with ECS read access)
#     * CloudTrail logs
#     * Terraform state file (which lives in S3)
#   - Secrets Manager stores them encrypted (KMS) and injects them at
#     container startup — the value is never written to disk or logs
#
# HOW IT WORKS IN ECS:
#   1. Secret stored here in Secrets Manager
#   2. ECS task definition references the ARN (not the value)
#   3. ECS task execution role has secretsmanager:GetSecretValue permission
#   4. At container startup, ECS fetches + injects the secret as an env var
#   5. The app reads it as a normal environment variable — zero code change
#
# INTERVIEW ANSWER:
#   "Secrets never appear in plaintext in task definitions or state files.
#    ECS fetches them from Secrets Manager at runtime using the task
#    execution role. The app code doesn't change — it still reads env vars."
# =============================================================================

# -----------------------------------------------------------------------------
# Database password
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "db_password" {
  name        = "taskhub/${var.environment}/db-password"
  description = "RDS PostgreSQL password for TaskHub ${var.environment}"

  # Prevent accidental deletion — remove this before terraform destroy
  # Set to 0 in dev to allow clean destroy without waiting 7 days
  recovery_window_in_days = var.environment == "prod" ? 7 : 0

  tags = {
    Name = "taskhub-${var.environment}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.db_password

  # Lifecycle: ignore external changes (e.g. manual rotation)
  # so Terraform doesn't overwrite a rotated password
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# -----------------------------------------------------------------------------
# JWT secret
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "taskhub/${var.environment}/jwt-secret"
  description = "JWT signing secret for TaskHub ${var.environment}"

  recovery_window_in_days = var.environment == "prod" ? 7 : 0

  tags = {
    Name = "taskhub-${var.environment}-jwt-secret"
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# -----------------------------------------------------------------------------
# Outputs — ARNs used by ecs.tf to reference secrets in task definitions
# (ARN, not value — ECS fetches the value at runtime)
# -----------------------------------------------------------------------------
output "db_password_secret_arn" {
  description = "ARN of the DB password secret — used in ECS task definition"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "jwt_secret_arn" {
  description = "ARN of the JWT secret — used in ECS task definition"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}
