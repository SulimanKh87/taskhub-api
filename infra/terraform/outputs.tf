output "alb_dns_name" {
  value       = aws_lb.this.dns_name
  description = "Public ALB DNS (if applied)"
}

output "ecr_repo_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository URL for the API image"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}
