# =============================================================================
# ecs.tf — ECS Cluster, Task Definitions, Services
#
# KEY CHANGE FROM ORIGINAL:
#   Before: secrets passed as plaintext `environment` blocks in task definition
#   After:  secrets passed as `secrets` blocks referencing Secrets Manager ARNs
#
# WHY THIS MATTERS:
#   Plaintext env vars appear in:
#     - AWS Console (ECS task definition page)
#     - CloudTrail API logs
#     - Terraform state file (stored in S3)
#   Secrets Manager ARNs reveal nothing — ECS fetches the value at runtime
#   using the task execution role.
# =============================================================================

# -----------------------------------------------------------------------------
# ECS Cluster
# -----------------------------------------------------------------------------
resource "aws_ecs_cluster" "main" {
  name = "taskhub-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "taskhub-${var.environment}-cluster" }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/taskhub-${var.environment}-api"
  retention_in_days = 14
  tags              = { Name = "taskhub-${var.environment}-api-logs" }
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/taskhub-${var.environment}-worker"
  retention_in_days = 14
  tags              = { Name = "taskhub-${var.environment}-worker-logs" }
}

resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/taskhub-${var.environment}-migration"
  retention_in_days = 7
  tags              = { Name = "taskhub-${var.environment}-migration-logs" }
}

# -----------------------------------------------------------------------------
# API Task Definition
# -----------------------------------------------------------------------------
resource "aws_ecs_task_definition" "api" {
  family                   = "taskhub-${var.environment}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  # iam.tf uses task_exec and task_role — reference those exact names
  execution_role_arn = aws_iam_role.task_exec.arn
  task_role_arn      = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENV", value = var.environment },
        { name = "APP_ENV", value = var.environment },
        { name = "APP_NAME", value = "taskhub-api" },
        { name = "APP_DEBUG", value = "false" },
        { name = "PORT", value = "8000" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "EVENT_BUS_NAME", value = var.event_bus_name },
        { name = "JWT_ALGORITHM", value = "HS256" },
        { name = "JWT_EXPIRE_MINUTES", value = "15" },
        { name = "JWT_REFRESH_DAYS", value = "7" },
        { name = "DB_POOL_SIZE", value = "5" },
        { name = "DB_MAX_OVERFLOW", value = "5" },
        { name = "DB_POOL_TIMEOUT", value = "30" },
        { name = "DB_POOL_RECYCLE_SECONDS", value = "1800" },
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        }
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])

  tags = { Name = "taskhub-${var.environment}-api" }
}

# -----------------------------------------------------------------------------
# Worker Task Definition
# -----------------------------------------------------------------------------
resource "aws_ecs_task_definition" "worker" {
  family                   = "taskhub-${var.environment}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.task_exec.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.api_image
      essential = true

      command = [
        "celery", "-A", "app.workers.celery_app:celery_app",
        "worker", "--loglevel=info", "--concurrency=2"
      ]

      environment = [
        { name = "ENV", value = var.environment },
        { name = "APP_ENV", value = var.environment },
        { name = "AWS_REGION", value = var.aws_region },
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.db_password.arn
        },
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  tags = { Name = "taskhub-${var.environment}-worker" }
}

# -----------------------------------------------------------------------------
# API ECS Service
# -----------------------------------------------------------------------------
resource "aws_ecs_service" "api" {
  name            = "taskhub-${var.environment}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count

  capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  force_new_deployment = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_iam_role.task_exec]

  tags = { Name = "taskhub-${var.environment}-api" }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# -----------------------------------------------------------------------------
# Worker ECS Service — FARGATE_SPOT for cost savings
# -----------------------------------------------------------------------------
resource "aws_ecs_service" "worker" {
  name            = "taskhub-${var.environment}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count

  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 1
  }

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = true
  }

  force_new_deployment = true

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_iam_role.task_exec]

  tags = { Name = "taskhub-${var.environment}-worker" }
}
