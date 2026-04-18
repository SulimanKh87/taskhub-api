# docs/AWS_DEPLOY.md
# ☁️ AWS Deployment Checklist

Complete step-by-step guide to deploy TaskHub to AWS for the first time.
Run these steps **after all 8 milestones are complete**.

> ⚠️ Running this will create real AWS resources and incur charges (~$66/month).
> Run `terraform destroy` when done to stop all charges.

---

## Prerequisites

```bash
# Verify tools are installed
aws --version          # AWS CLI v2
terraform --version    # >= 1.6.0
docker --version       # Docker Desktop or Engine
git --version
```

Configure AWS credentials:
```bash
aws configure
# AWS Access Key ID:     your-access-key-id
# AWS Secret Access Key: your-secret-access-key
# Default region:        eu-central-1
# Default output format: json
```

Verify access:
```bash
aws sts get-caller-identity
# Should return your account ID and ARN
```

---

## Step 1 — Update Placeholders

Search your repo for `123456789012` and replace with your real AWS account ID:

```bash
# Find all occurrences
grep -r "123456789012" . --include="*.tf" --include="*.yaml" --include="*.yml" --include="*.json"
```

Files to update:
```
infra/terraform/variables.tf          → api_image default value
infra/terraform/terraform.tfvars.example → api_image
k8s/deployment-api.yaml               → image field
k8s/deployment-worker.yaml            → image field
helm/taskhub/values.yaml              → api.image.repository + worker.image.repository
```

Also update `terraform.tfvars.example`:
```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
# Edit terraform.tfvars with real values — this file is gitignored
```

---

## Step 2 — Bootstrap Remote State (One Time Only)

This creates the S3 bucket and DynamoDB table that Terraform uses to
store state. Must be done before `terraform init`.

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="taskhub-terraform-state-${ACCOUNT_ID}"

# Create S3 bucket for state storage
aws s3 mb s3://${BUCKET_NAME} --region eu-central-1

# Enable versioning (allows state recovery if corrupted)
aws s3api put-bucket-versioning \
  --bucket ${BUCKET_NAME} \
  --versioning-configuration Status=Enabled

# Enable encryption at rest
aws s3api put-bucket-encryption \
  --bucket ${BUCKET_NAME} \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name taskhub-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-central-1

echo "Bootstrap complete. Bucket: ${BUCKET_NAME}"
```

Update `infra/terraform/provider.tf` with your bucket name:
```hcl
backend "s3" {
  bucket         = "taskhub-terraform-state-YOUR_ACCOUNT_ID"  # ← update this
  key            = "taskhub/dev/terraform.tfstate"
  region         = "eu-central-1"
  encrypt        = true
  dynamodb_table = "taskhub-terraform-locks"
}
```

---

## Step 3 — Terraform Init + Apply

```bash
cd infra/terraform

# Initialize — connects to S3 backend
terraform init

# Preview what will be created (read carefully)
terraform plan

# Create all infrastructure (~8-10 minutes)
terraform apply
# Type "yes" when prompted

# Save outputs for later steps
terraform output
```

Key outputs you will need:
```
ecr_api_repo_url      → for pushing images
ecr_worker_repo_url   → for pushing images
alb_dns_name          → your API's public URL
ecs_cluster_name      → for ECS commands
```

---

## Step 4 — Push Docker Images to ECR

```bash
cd ../../   # back to repo root

# Authenticate Docker to ECR
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-central-1.amazonaws.com

# Build and push (uses the automated script)
./scripts/push-to-ecr.sh
```

Verify images are in ECR:
```bash
aws ecr describe-images \
  --repository-name taskhub-dev-api \
  --region eu-central-1 \
  --query 'imageDetails[0].{Tag: imageTags[0], Pushed: imagePushedAt}'
```

---

## Step 5 — Run Database Migrations

```bash
# Runs Alembic migrations as a one-off ECS task
./scripts/run-migrations.sh

# Verify migrations completed
aws logs tail /ecs/taskhub-dev-migration \
  --region eu-central-1 \
  --since 10m
# Should see: "Running upgrade -> 0001, init schema"
```

---

## Step 6 — Verify Deployment

```bash
# Get your ALB DNS name
ALB_URL=$(cd infra/terraform && terraform output -raw alb_dns_name)

# Health check
curl http://${ALB_URL}/health
# {"status": "ok", "app": "TaskHub API"}

# Register a user
curl -X POST http://${ALB_URL}/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "StrongPass123"}'

# Login
curl -X POST http://${ALB_URL}/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=StrongPass123"
```

---

## Step 7 — Verify Monitoring

```bash
# Check CloudWatch alarms are created
aws cloudwatch describe-alarms \
  --alarm-name-prefix "taskhub-dev" \
  --region eu-central-1 \
  --query 'MetricAlarms[].{Name: AlarmName, State: StateValue}'

# Confirm SNS email subscription
# Check your inbox for a confirmation email from AWS SNS
# Click confirm — alarms won't notify until you do this
```

---

## Step 8 — Optional: Configure kubectl for EKS

Only needed if you want to test the Kubernetes manifests:

```bash
# Configure kubectl to talk to the EKS cluster
aws eks update-kubeconfig \
  --region eu-central-1 \
  --name $(cd infra/terraform && terraform output -raw eks_cluster_name)

# Verify connection
kubectl get nodes

# Create namespace and secrets
kubectl create namespace taskhub

kubectl create secret generic taskhub-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=JWT_SECRET="your-jwt-secret" \
  --from-literal=REDIS_BROKER="redis://..." \
  -n taskhub

# Deploy with kubectl
kubectl apply -f k8s/ -n taskhub

# Or deploy with Helm
helm install taskhub ./helm/taskhub \
  --namespace taskhub \
  --set api.image.tag=$(git rev-parse --short HEAD)
```

---

## Teardown — Stop All Charges

```bash
cd infra/terraform
terraform destroy
# Type "yes" when prompted
# Takes ~5-8 minutes
```

After destroy, only ECR storage (~$0.05/month) and the S3 state bucket
(~$0.01/month) remain. Delete those manually if you want $0 cost:

```bash
# Empty and delete ECR repos
aws ecr delete-repository --repository-name taskhub-dev-api --force --region eu-central-1
aws ecr delete-repository --repository-name taskhub-dev-worker --force --region eu-central-1

# Empty and delete state bucket (CAREFUL — this deletes your Terraform state)
aws s3 rm s3://taskhub-terraform-state-YOUR_ACCOUNT_ID --recursive
aws s3 rb s3://taskhub-terraform-state-YOUR_ACCOUNT_ID
```

---

## Troubleshooting

**`terraform init` fails with backend error:**
Check the S3 bucket name in `provider.tf` matches the bucket you created.

**ECS tasks keep restarting:**
```bash
aws logs tail /ecs/taskhub-dev-api --since 10m --region eu-central-1
# Read INCIDENTS.md → Incident 1 for full diagnosis steps
```

**Images not found in ECR:**
```bash
# Re-authenticate Docker (token expires every 12 hours)
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.eu-central-1.amazonaws.com
```

**Migrations failed:**
```bash
aws logs tail /ecs/taskhub-dev-migration --follow --region eu-central-1
```

For all other issues, see `docs/INCIDENTS.md` and `docs/OPERATIONS.md`.
