# =============================================================================
# eks.tf — Amazon EKS Cluster (Kubernetes on AWS)
#
# WHY EKS vs ECS (interview question):
#   ECS: simpler, cheaper, AWS-native, less ecosystem
#   EKS: industry standard, Kubernetes skills transfer anywhere,
#        required at larger Israeli tech companies (Monday, Wix, etc.)
#
# DECISION:
#   TaskHub uses ECS in production (cost-effective for a single service).
#   This file exists to demonstrate EKS knowledge for interviews.
#   The k8s/ and helm/ directories are the matching application manifests.
#
# NOTE: Do not apply this file until the final AWS deployment step.
#       Comment out this file if you only want to deploy ECS.
# =============================================================================

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "taskhub-${var.environment}-eks"
  cluster_version = "1.29"

  # Use the VPC and subnets defined in main.tf directly
  # (no separate networking module — resources are in root module)
  vpc_id     = aws_vpc.this.id
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  cluster_endpoint_public_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    default = {
      name           = "taskhub-${var.environment}-nodes"
      instance_types = ["t3.small"]

      capacity_type = var.environment == "prod" ? "ON_DEMAND" : "SPOT"

      min_size     = 1
      max_size     = 4
      desired_size = 2

      disk_size = 20

      labels = {
        Environment = var.environment
        NodeGroup   = "default"
      }

      tags = {
        Name = "taskhub-${var.environment}-node"
      }
    }
  }

  enable_cluster_creator_admin_permissions = true

  tags = {
    Name = "taskhub-${var.environment}-eks"
  }
}

output "eks_cluster_name" {
  description = "EKS cluster name — use with aws eks update-kubeconfig"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API server endpoint"
  value       = module.eks.cluster_endpoint
}
