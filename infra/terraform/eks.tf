# =============================================================================
# eks.tf — Amazon EKS Cluster (Kubernetes on AWS)
#
# WHY EKS vs ECS (interview question):
#
#   ECS (what TaskHub uses today):
#     + Simpler — AWS-native, less operational overhead
#     + Cheaper — no control plane cost ($0.10/hr per EKS cluster)
#     + Faster to set up for small teams
#     - AWS-specific — not portable to other clouds or on-prem
#     - Less ecosystem — no Helm, no kubectl plugins
#
#   EKS (this file):
#     + Industry standard — Kubernetes skills transfer anywhere
#     + Huge ecosystem: Helm, Prometheus operator, Argo CD, etc.
#     + Better for multi-team, multi-service platforms
#     + Required at larger Israeli tech companies (Monday, Wix, etc.)
#     - More complex — need to manage node groups, add-ons, RBAC
#     - More expensive — control plane + node costs
#
# DECISION:
#   TaskHub uses ECS in production (cost-effective for a single service).
#   This file exists to demonstrate EKS knowledge for interviews.
#   The k8s/ and helm/ directories are the matching application manifests.
#
# NOTE: Do not apply this file until the final AWS deployment step.
# =============================================================================

# -----------------------------------------------------------------------------
# EKS Cluster
# Using the community module — saves ~200 lines of IAM/addon boilerplate
# -----------------------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "taskhub-${var.environment}-eks"
  cluster_version = "1.29"

  # Deploy into the same VPC as ECS/RDS
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  # Allow kubectl access from the internet (dev cluster)
  # In production: set to false and use VPN or bastion
  cluster_endpoint_public_access = true

  # Add-ons managed by AWS (auto-updates, no manual version pinning)
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
    # EBS CSI driver — required for PersistentVolumes backed by EBS
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  # -------------------------------------------------------------------------
  # Node group — EC2 instances that run your pods
  #
  # Why t3.small?
  #   - Smallest instance that runs EKS system pods + your app pods
  #   - t3.micro is too small (EKS system pods alone consume ~900MB)
  #   - Spot instances: same specs, up to 70% cheaper
  #     Risk: spot interruption — acceptable for dev, not for prod
  # -------------------------------------------------------------------------
  eks_managed_node_groups = {
    default = {
      name           = "taskhub-${var.environment}-nodes"
      instance_types = ["t3.small"]

      # Spot instances for cost savings in dev
      # Change to ON_DEMAND for production
      capacity_type = var.environment == "prod" ? "ON_DEMAND" : "SPOT"

      min_size     = 1
      max_size     = 4
      desired_size = 2

      # Disk size per node
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

  # -------------------------------------------------------------------------
  # IAM — grant your local IAM user kubectl access
  # Replace with your actual AWS IAM user ARN
  # -------------------------------------------------------------------------
  enable_cluster_creator_admin_permissions = true

  tags = {
    Name = "taskhub-${var.environment}-eks"
  }
}

# -----------------------------------------------------------------------------
# Output — use this to configure kubectl:
#   aws eks update-kubeconfig \
#     --region eu-central-1 \
#     --name $(terraform output -raw eks_cluster_name)
# -----------------------------------------------------------------------------
output "eks_cluster_name" {
  description = "EKS cluster name — use with aws eks update-kubeconfig"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS API server endpoint"
  value       = module.eks.cluster_endpoint
}
