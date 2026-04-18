#!/bin/bash
# scripts/push-to-ecr.sh
# =============================================================================
# ECR Push Script - TaskHub API
# =============================================================================
# Usage:
#   ./scripts/push-to-ecr.sh
#
# Prerequisites:
#   - AWS CLI configured
#   - Docker running
#   - Terraform applied (ECR repos exist)
# =============================================================================

set -e  # Exit on error

# -----------------------
# Configuration
# -----------------------
REGION="eu-central-1"
PROJECT="taskhub"
ENV="dev"

# Get ECR URLs from Terraform outputs
cd infra/terraform
API_REPO=$(terraform output -raw ecr_api_repo_url)
WORKER_REPO=$(terraform output -raw ecr_worker_repo_url)
REGISTRY=$(echo "$API_REPO" | cut -d'/' -f1)
cd ../..

echo "📦 ECR Push Script"
echo "===================="
echo "Region: $REGION"
echo "API Repo: $API_REPO"
echo "Worker Repo: $WORKER_REPO"
echo ""

# -----------------------
# Step 1: ECR Login
# -----------------------
echo "🔐 Authenticating to ECR..."
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$REGISTRY"

if [ $? -ne 0 ]; then
  echo "❌ ECR login failed. Check AWS credentials."
  exit 1
fi

echo "✅ ECR login successful"
echo ""

# -----------------------
# Step 2: Build Images
# -----------------------
echo "🏗️  Building Docker images..."

echo "Building API image..."
docker build -t taskhub-api:latest .

echo "Building Worker image..."
docker build -t taskhub-worker:latest .

echo "✅ Images built successfully"
echo ""

# -----------------------
# Step 3: Tag Images
# -----------------------
echo "🏷️  Tagging images for ECR..."

docker tag taskhub-api:latest "$API_REPO:latest"
docker tag taskhub-worker:latest "$WORKER_REPO:latest"

echo "✅ Images tagged successfully"
echo ""

# -----------------------
# Step 4: Push Images
# -----------------------
echo "📤 Pushing images to ECR..."

echo "Pushing API image..."
docker push "$API_REPO:latest"

echo "Pushing Worker image..."
docker push "$WORKER_REPO:latest"

echo "✅ Images pushed successfully"
echo ""

# -----------------------
# Step 5: Verify
# -----------------------
echo "🔍 Verifying images in ECR..."

aws ecr describe-images \
  --repository-name "$PROJECT-$ENV-api" \
  --region "$REGION" \
  --query 'imageDetails[0].imageTags[0]' \
  --output text

aws ecr describe-images \
  --repository-name "$PROJECT-$ENV-worker" \
  --region "$REGION" \
  --query 'imageDetails[0].imageTags[0]' \
  --output text

echo ""
echo "✅ ECR Push Complete!"
echo ""
echo "Next steps:"
echo "1. Update infra/terraform/terraform.tfvars with ECR image URIs"
echo "2. Run 'terraform apply' to update ECS task definitions"