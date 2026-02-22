# =============================================================================
# infra/terraform/ecs.tf
# =============================================================================
# ECS Fargate cluster, task definitions, and services
#
# Extracted from main.tf for better organization (Milestone 3)
#
# Resources:
# - ECS cluster with containerInsights enabled
# - API task definition (Fargate, port 8000, health check)
# - Worker task definition (Fargate, Celery, no ports)
# - API service (wired to ALB target group)
# - Worker service (outbound only)
# =============================================================================

# -------------------------
# ECS Cluster
# -------------------------
resource "aws_ecs_cluster" "this" {
  name = "${local.name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${local.name}-cluster"
  }
}

# -------------------------
# ECS Task Definition: API
# -------------------------
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.task_exec.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = var.api_image
    essential = true

    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENV",          value = "prod" },
      { name = "JWT_SECRET",   value = var.jwt_secret },
      { name = "DATABASE_URL", value = local.database_url },
      { name = "REDIS_BROKER", value = local.redis_broker }
    ]

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.api.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])

  tags = {
    Name = "${local.name}-api-task"
  }
}

# -------------------------
# ECS Service: API
# -------------------------
resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

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

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy_attachment.task_exec
  ]

  tags = {
    Name = "${local.name}-api-service"
  }
}

# -------------------------
# ECS Task Definition: Worker
# -------------------------
resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.task_exec.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = var.worker_image
    essential = true

    command = ["celery", "-A", "app.workers.celery_app.celery_app", "worker", "--loglevel=INFO"]

    environment = [
      { name = "ENV",          value = "prod" },
      { name = "JWT_SECRET",   value = var.jwt_secret },
      { name = "DATABASE_URL", value = local.database_url },
      { name = "REDIS_BROKER", value = local.redis_broker }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.worker.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "ecs"
      }
    }
  }])

  tags = {
    Name = "${local.name}-worker-task"
  }
}

# -------------------------
# ECS Service: Worker
# -------------------------
resource "aws_ecs_service" "worker" {
  name            = "${local.name}-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.task_exec
  ]

  tags = {
    Name = "${local.name}-worker-service"
  }
}
