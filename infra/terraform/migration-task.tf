# =============================================================================
# infra/terraform/migration-task.tf
# =============================================================================
# ECS task definition for running Alembic database migrations
#
# Usage:
#   aws ecs run-task \
#     --cluster taskhub-dev-cluster \
#     --task-definition taskhub-dev-migration \
#     --launch-type FARGATE \
#     --network-configuration "awsvpcConfiguration={subnets=[...],securityGroups=[...],assignPublicIp=ENABLED}"
# =============================================================================

resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_exec.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([{
    name      = "migration"
    image     = var.api_image
    essential = true

    command = ["alembic", "upgrade", "head"]

    environment = [
      { name = "ENV", value = "prod" },
      { name = "JWT_SECRET", value = var.jwt_secret },
      { name = "DATABASE_URL", value = local.database_url },
      { name = "REDIS_BROKER", value = local.redis_broker }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.migration.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "migration"
      }
    }
  }])

  tags = {
    Name = "${local.name}-migration-task"
  }
}

resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${local.name}-migration"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name}-migration-logs"
  }
}
