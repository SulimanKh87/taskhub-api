# =============================================================================
# infra/terraform/iam.tf
# =============================================================================
# Two distinct IAM roles for ECS:
#
# task_exec  → used by ECS AGENT (pull ECR images, write CloudWatch logs)
# task_role  → used by YOUR APP CODE (future: SES, S3, Secrets Manager)
# =============================================================================

data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# -------------------------
# Execution Role (ECS agent)
# -------------------------
resource "aws_iam_role" "task_exec" {
  name               = "${local.name}-ecs-task-exec"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = { Name = "${local.name}-ecs-task-exec" }
}

resource "aws_iam_role_policy_attachment" "task_exec" {
  role       = aws_iam_role.task_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# -------------------------
# Task Role (your app code)
# -------------------------
resource "aws_iam_role" "task_role" {
  name               = "${local.name}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = { Name = "${local.name}-ecs-task-role" }
}

resource "aws_iam_role_policy" "task_role_policy" {
  name = "${local.name}-task-role-policy"
  role = aws_iam_role.task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # ECS Exec
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel"
        ]
        Resource = "*"
      },  # ← Fixed: comma INSIDE array
      {
        # EventBridge
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = "arn:aws:events:${var.aws_region}:*:event-bus/default"
      }
    ]
  })
}

resource "aws_iam_role_policy" "task_secrets_policy" {
  name = "${local.name}-task-secrets-policy"
  role = aws_iam_role.task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_password.arn,
          aws_secretsmanager_secret.jwt_secret.arn
        ]
      }
    ]
  })
}