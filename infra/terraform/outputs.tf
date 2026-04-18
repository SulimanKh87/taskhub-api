# infra/terraform/outputs.tf

output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "Public ALB DNS (if applied)"
}

output "ecr_api_repo_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository URL for the API image"
}

output "ecr_worker_repo_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "ECR repository URL for the worker image"
}

output "ecs_cluster_name" {
  # ecs.tf uses aws_ecs_cluster.main (not .this)
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name"
}

output "api_service_name" {
  value       = aws_ecs_service.api.name
  description = "ECS service name for API"
}

output "worker_service_name" {
  value       = aws_ecs_service.worker.name
  description = "ECS service name for worker"
}

output "db_endpoint" {
  value       = aws_db_instance.postgres.address
  description = "RDS Postgres endpoint (hostname)"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "ElastiCache Redis endpoint (hostname)"
}

output "public_subnet_a_id" {
  value       = aws_subnet.public_a.id
  description = "Public subnet A ID"
}

output "public_subnet_b_id" {
  value       = aws_subnet.public_b.id
  description = "Public subnet B ID"
}

output "api_security_group_id" {
  value       = aws_security_group.api.id
  description = "API security group ID"
}

output "migration_task_family" {
  value       = aws_ecs_task_definition.migration.family
  description = "ECS task definition family for running Alembic migrations"
}

output "migration_task_arn" {
  value       = aws_ecs_task_definition.migration.arn
  description = "Full ARN of the migration task definition (includes revision)"
}

output "aws_region" {
  value       = var.aws_region
  description = "AWS region for all resources"
}

output "lambda_function_name" {
  value       = aws_lambda_function.resume_booster.function_name
  description = "Lambda function name for resume booster"
}

output "eventbridge_rule_name" {
  value       = aws_cloudwatch_event_rule.task_created.name
  description = "EventBridge rule name for task created events"
}
