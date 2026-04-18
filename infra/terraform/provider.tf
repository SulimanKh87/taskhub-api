# =============================================================================
# provider.tf — AWS Provider + Remote State Backend
#
# WHY REMOTE STATE?
#   - Local state only works on one machine
#   - S3 backend allows any machine (CI, teammate, you from another laptop)
#     to run terraform plan/apply against the same state
#   - DynamoDB locking prevents two people (or two CI jobs) running apply
#     at the same time and corrupting state
#
# INTERVIEW ANSWER:
#   "I use S3 for state storage and DynamoDB for state locking.
#    Without locking, two concurrent applies can corrupt the state file."
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # -------------------------------------------------------------------------
  # Remote state backend
  #
  # Before first use, create these manually (one-time bootstrap):
  #   aws s3 mb s3://taskhub-terraform-state-<your-account-id> --region eu-central-1
  #   aws dynamodb create-table \
  #     --table-name taskhub-terraform-locks \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST \
  #     --region eu-central-1
  #
  # Why not manage the bucket with Terraform itself?
  # Because Terraform needs the backend to exist BEFORE it can store state —
  # chicken-and-egg problem. Bootstrap manually, manage everything else with TF.
  # -------------------------------------------------------------------------
  backend "s3" {
    bucket  = "taskhub-terraform-state" # replace with your bucket name
    key     = "taskhub/dev/terraform.tfstate"
    region  = "eu-central-1"
    encrypt = true # SSE-S3 encryption at rest

    # DynamoDB table for state locking
    # Prevents concurrent applies from corrupting state
    dynamodb_table = "taskhub-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  # Tag every resource created by Terraform automatically
  # Useful for cost allocation, filtering in console, and compliance
  default_tags {
    tags = {
      Project     = "taskhub"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
