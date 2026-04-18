#!/bin/bash
# scripts//run-migrations.sh
# =============================================================================
# Run Alembic migrations on ECS
# =============================================================================
# Usage: ./scripts/run-migrations.sh
# =============================================================================

set -e

# Get configuration from Terraform outputs
cd infra/terraform
REGION=$(terraform output -raw aws_region 2>/dev/null || echo "eu-central-1")
CLUSTER=$(terraform output -raw ecs_cluster_name)
TASK_DEF=$(terraform output -raw migration_task_arn) # Runs exact revision that Terraform created but using migration_task_family will update the version everytime
cd ../..

echo "🗄️  Running Alembic migrations on ECS..."
echo ""

# Get network configuration from Terraform
cd infra/terraform

echo "📡 Getting network configuration..."
SUBNET_A=$(terraform output -raw public_subnet_a_id 2>/dev/null || echo "")
SUBNET_B=$(terraform output -raw public_subnet_b_id 2>/dev/null || echo "")
API_SG=$(terraform output -raw api_security_group_id 2>/dev/null || echo "")

# Fallback: parse from terraform state if outputs don't exist
if [ -z "$SUBNET_A" ]; then
  echo "⚠️  Outputs not found, parsing terraform state..."
  SUBNET_A=$(terraform show -json | jq -r '.values.root_module.resources[] | select(.address=="aws_subnet.public_a") | .values.id')
  SUBNET_B=$(terraform show -json | jq -r '.values.root_module.resources[] | select(.address=="aws_subnet.public_b") | .values.id')
  API_SG=$(terraform show -json | jq -r '.values.root_module.resources[] | select(.address=="aws_security_group.api") | .values.id')
fi

echo "Subnets: $SUBNET_A, $SUBNET_B"
echo "Security Group: $API_SG"
echo ""

cd ../..

# Run migration task
echo "🚀 Starting migration task..."
TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_A,$SUBNET_B],securityGroups=[$API_SG],assignPublicIp=ENABLED}" \
  --region "$REGION" \
  --query 'tasks[0].taskArn' \
  --output text)

echo "Task ARN: $TASK_ARN"
echo ""

# Wait for task to complete
echo "⏳ Waiting for migration to complete..."
aws ecs wait tasks-stopped \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --region "$REGION"

# Check exit code
EXIT_CODE=$(aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --region "$REGION" \
  --query 'tasks[0].containers[0].exitCode' \
  --output text)

if [ "$EXIT_CODE" = "0" ]; then
  echo "✅ Migration completed successfully!"
else
  echo "❌ Migration failed with exit code: $EXIT_CODE"
  echo ""
  echo "Check logs:"
  echo "aws logs tail /ecs/taskhub-dev-migration --follow --region $REGION"
  exit 1
fi
