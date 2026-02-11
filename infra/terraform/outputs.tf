# output.tf
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
  value       = aws_ecs_cluster.this.name
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
