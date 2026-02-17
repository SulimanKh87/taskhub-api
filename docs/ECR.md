# 🐳 ECR Integration Guide

This document explains how to build, tag, and push Docker images to AWS Elastic Container Registry (ECR).

---

## 📋 Prerequisites

1. **AWS CLI installed and configured**
```bash
   aws --version
   aws configure  # Set region: eu-central-1
```

2. **Docker installed**
```bash
   docker --version
```

3. **Terraform applied (ECR repos created)**
```bash
   cd infra/terraform
   terraform init
   terraform apply  # Creates ECR repositories
```

---

## 🏗️ Step 1: Get ECR Repository URLs

After applying Terraform, get your ECR repository URLs:
```bash
cd infra/terraform
terraform output ecr_api_repo_url
terraform output ecr_worker_repo_url
```

**Example output:**
```
ecr_api_repo_url = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api"
ecr_worker_repo_url = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker"
```

**Save these URLs — you'll need them for tagging.**

---

## 🔐 Step 2: Authenticate Docker to ECR

Log in to your ECR registry:
```bash
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com
```

**Expected output:**
```
Login Succeeded
```

> **Note:** Replace `123456789012` with your actual AWS account ID.
> 
> **Token expires after 12 hours** — you'll need to re-authenticate if you see auth errors.

---

## 🐳 Step 3: Build Docker Images

### Build API Image
```bash
# From project root
cd taskhub-api/

docker build -t taskhub-api:latest .
```

**What happens:**
- Uses `Dockerfile` in project root
- Installs dependencies from `requirements.txt`
- Creates non-root user `appuser`
- Exposes port 8000
- Sets CMD to run FastAPI with uvicorn

**Verify:**
```bash
docker images | grep taskhub-api
```

Expected output:
```
taskhub-api    latest    abc123def456    2 minutes ago    450MB
```

---

### Build Worker Image

The worker uses the **same Dockerfile** but runs Celery instead of FastAPI:
```bash
docker build -t taskhub-worker:latest .
```

> **Note:** Both API and worker use the same base image. The difference is the runtime command:
> - **API**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
> - **Worker**: `celery -A app.workers.celery_app worker --loglevel=INFO`
> 
> The command is controlled by ECS task definition, not the Dockerfile.

**Verify:**
```bash
docker images | grep taskhub-worker
```

Expected output:
```
taskhub-worker    latest    xyz789abc123    1 minute ago    450MB
```

---

## 🏷️ Step 4: Tag Images for ECR

Tag your local images with the ECR repository URLs:

### Tag API Image
```bash
docker tag taskhub-api:latest \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:latest
```

### Tag Worker Image
```bash
docker tag taskhub-worker:latest \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker:latest
```

**Verify tags:**
```bash
docker images | grep ecr
```

Expected output:
```
123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api      latest    abc123def456
123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker   latest    xyz789abc123
```

---

## 📤 Step 5: Push Images to ECR

### Push API Image
```bash
docker push 123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:latest
```

**Expected output:**
```
The push refers to repository [123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api]
5f70bf18a086: Pushed
latest: digest: sha256:abc123... size: 1234
```

### Push Worker Image
```bash
docker push 123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker:latest
```

**Expected output:**
```
The push refers to repository [123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker]
5f70bf18a086: Layer already exists
latest: digest: sha256:xyz789... size: 1234
```

> **Note:** Worker push is faster because layers are shared with API image.

---

## ✅ Step 6: Verify Images in ECR

### Via AWS CLI
```bash
aws ecr describe-images \
  --repository-name taskhub-dev-api \
  --region eu-central-1

aws ecr describe-images \
  --repository-name taskhub-dev-worker \
  --region eu-central-1
```

**Expected output:**
```json
{
    "imageDetails": [
        {
            "imageTags": ["latest"],
            "imageSizeInBytes": 450123456,
            "imagePushedAt": "2025-02-16T10:30:00+00:00",
            "imageDigest": "sha256:abc123..."
        }
    ]
}
```

### Via AWS Console

1. Go to **AWS Console** → **ECR**
2. Select region: **eu-central-1**
3. You should see:
   - `taskhub-dev-api` (1 image with tag `latest`)
   - `taskhub-dev-worker` (1 image with tag `latest`)

---

## 🔄 Updating Images (CI/CD)

When you make code changes:
```bash
# 1. Rebuild
docker build -t taskhub-api:latest .

# 2. Re-tag with new version
docker tag taskhub-api:latest \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:v1.0.1

# 3. Push new version
docker push 123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:v1.0.1

# 4. Update ECS service to use new image
aws ecs update-service \
  --cluster taskhub-dev-cluster \
  --service taskhub-dev-api \
  --force-new-deployment
```

---

## 🤖 Automated Push Script

Instead of running commands manually, use the provided helper script:
```bash
# Make script executable (first time only)
chmod +x scripts/push-to-ecr.sh

# Run the script
./scripts/push-to-ecr.sh
```

**What it does:**
1. Authenticates to ECR
2. Builds both images
3. Tags them with ECR URLs
4. Pushes to ECR
5. Verifies images are present

---

## 🧹 Cleanup (Optional)

Remove old/untagged images to save costs:
```bash
# List untagged images
aws ecr list-images \
  --repository-name taskhub-dev-api \
  --filter tagStatus=UNTAGGED \
  --region eu-central-1

# Delete untagged images
aws ecr batch-delete-image \
  --repository-name taskhub-dev-api \
  --image-ids imageDigest=sha256:xxxxx \
  --region eu-central-1
```

> **Note:** ECR lifecycle policies (defined in `infra/terraform/ecr.tf`) will automatically:
> - Keep only the last 5 tagged images
> - Delete untagged images after 1 day

---

## 🚨 Troubleshooting

### Error: "no basic auth credentials"
**Solution:** Re-authenticate to ECR (login expires after 12 hours)
```bash
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com
```

### Error: "repository does not exist"
**Solution:** Apply Terraform to create ECR repos
```bash
cd infra/terraform
terraform apply
```

### Error: "denied: User is not authorized"
**Solution:** Check IAM permissions for ECR
```bash
aws iam get-user
# Ensure user has AmazonEC2ContainerRegistryFullAccess policy
```

### Error: "denied: Your authorization token has expired"
**Solution:** ECR tokens expire after 12 hours. Re-authenticate:
```bash
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.eu-central-1.amazonaws.com
```

### Error: "image with reference X already exists"
**Solution:** This is normal — you're overwriting the `latest` tag. Continue.

---

## 📚 Next Steps

After images are in ECR:
1. Update `infra/terraform/terraform.tfvars` with real ECR image URIs
2. Run `terraform apply` to update ECS task definitions
3. ECS will pull images from ECR and run your containers

**Example `terraform.tfvars` update:**
```hcl
api_image    = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-api:latest"
worker_image = "123456789012.dkr.ecr.eu-central-1.amazonaws.com/taskhub-dev-worker:latest"
```

---

## 🔗 References

- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/)
- [Terraform AWS ECR Module](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository)
- [ECR Lifecycle Policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)