// =============================================================================
// Jenkinsfile — TaskHub API Pipeline (Declarative syntax)
//
// WHY THIS FILE EXISTS:
//   This project uses GitHub Actions as its primary CI/CD tool.
//   This Jenkinsfile exists to demonstrate familiarity with Jenkins —
//   required for ~40% of Israeli DevOps interviews.
//
// GITHUB ACTIONS vs JENKINS:
//   GitHub Actions:
//     + SaaS — zero infrastructure to maintain
//     + Native GitHub integration (PRs, branch protection, secrets)
//     + Free for public repos, cheap for private
//     - Less flexible for complex enterprise pipelines
//     - Harder to self-host in air-gapped environments
//
//   Jenkins:
//     + Self-hosted — full control, works air-gapped
//     + Huge plugin ecosystem (1800+ plugins)
//     + Better for complex multi-team enterprise pipelines
//     - Requires maintaining Jenkins server (updates, plugins, storage)
//     - More setup overhead
//
// INTERVIEW ANSWER:
//   "I chose GitHub Actions for this project because it's zero-maintenance
//    and integrates natively with GitHub. In an enterprise environment with
//    air-gapped infrastructure or complex multi-repo pipelines, I'd use Jenkins."
//
// PIPELINE MIRRORS deploy.yml:
//   Test → Build → Scan → Push to ECR → Deploy to ECS → Rollback on failure
// =============================================================================

pipeline {
    agent any

    // -------------------------------------------------------------------------
    // Environment variables available to all stages
    // Secrets injected via Jenkins Credentials (never hardcoded here)
    // -------------------------------------------------------------------------
    environment {
        AWS_REGION          = 'eu-central-1'
        ECR_API_REPO        = 'taskhub-dev-api'
        ECR_WORKER_REPO     = 'taskhub-dev-worker'
        ECS_CLUSTER         = 'taskhub-dev-cluster'
        ECS_API_SERVICE     = 'taskhub-dev-api'
        ECS_WORKER_SERVICE  = 'taskhub-dev-worker'

        // Jenkins credentials store — never hardcode secrets in Jenkinsfile
        // Add these in: Jenkins → Manage → Credentials
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-access-key')
    }

    // -------------------------------------------------------------------------
    // Build triggers
    // -------------------------------------------------------------------------
    triggers {
        // Poll SCM every 5 minutes (use GitHub webhook in production instead)
        // pollSCM('H/5 * * * *')
        githubPush()    // requires GitHub plugin + webhook configured
    }

    options {
        // Keep last 10 builds — don't fill disk with old logs
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Fail pipeline if any stage takes longer than 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Don't run concurrent builds on the same branch
        disableConcurrentBuilds()
        // Add timestamps to console output
        timestamps()
    }

    stages {

        // =====================================================================
        // Stage 1: Test
        // Requires: Docker (for PostgreSQL + Redis containers)
        // =====================================================================
        stage('Test') {
            steps {
                echo 'Running Python tests with real PostgreSQL and Redis...'

                // Start dependency containers
                sh '''
                    docker run -d --name ci-postgres \
                        -e POSTGRES_USER=taskhub \
                        -e POSTGRES_PASSWORD=taskhub \
                        -e POSTGRES_DB=taskhub \
                        -p 5432:5432 \
                        postgres:16

                    docker run -d --name ci-redis \
                        -p 6379:6379 \
                        redis:7

                    # Wait for PostgreSQL to be ready
                    sleep 5
                '''

                // Run tests in a Python container
                sh '''
                    pip install -r requirements.txt black ruff

                    # Linting
                    black --check .
                    ruff check .

                    # Create test env
                    echo "ENV=test" > .env
                    echo "DATABASE_URL=postgresql+asyncpg://taskhub:taskhub@localhost:5432/taskhub" >> .env
                    echo "REDIS_BROKER=redis://localhost:6379/0" >> .env
                    echo "JWT_SECRET=ci_test_secret" >> .env
                    echo "JWT_ALGORITHM=HS256" >> .env

                    # Run tests
                    PYTHONPATH=. pytest -v app/tests --disable-warnings
                '''
            }

            post {
                always {
                    // Clean up containers regardless of test result
                    sh '''
                        docker rm -f ci-postgres ci-redis || true
                    '''
                }
            }
        }

        // =====================================================================
        // Stage 2: Terraform Validate
        // =====================================================================
        stage('Terraform Validate') {
            steps {
                dir('infra/terraform') {
                    sh '''
                        terraform init -backend=false
                        terraform fmt -check -recursive
                        terraform validate
                    '''
                }
            }
        }

        // =====================================================================
        // Stage 3: Build Docker Image
        // =====================================================================
        stage('Build') {
            steps {
                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                echo "Building image with tag: ${env.IMAGE_TAG}"

                sh "docker build -t taskhub-api:${env.IMAGE_TAG} -t taskhub-api:latest ."
            }
        }

        // =====================================================================
        // Stage 4: Security Scan
        // Blocks pipeline on CRITICAL vulnerabilities
        // =====================================================================
        stage('Security Scan') {
            steps {
                echo 'Scanning image for vulnerabilities with Trivy...'

                sh '''
                    # Install Trivy if not available
                    which trivy || (
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    )

                    trivy image \
                        --exit-code 1 \
                        --severity CRITICAL \
                        --ignore-unfixed \
                        taskhub-api:${IMAGE_TAG}
                '''
            }
        }

        // =====================================================================
        // Stage 5: Push to ECR
        // Only runs on the main devops branch
        // =====================================================================
        stage('Push to ECR') {
            when {
                branch 'devops-sql-aws'
            }

            steps {
                script {
                    // Get ECR login token and registry URL
                    def loginCmd = sh(
                        script: "aws ecr get-login-password --region ${env.AWS_REGION}",
                        returnStdout: true
                    ).trim()

                    def registry = sh(
                        script: "aws sts get-caller-identity --query Account --output text",
                        returnStdout: true
                    ).trim() + ".dkr.ecr.${env.AWS_REGION}.amazonaws.com"

                    env.ECR_REGISTRY = registry

                    sh """
                        echo ${loginCmd} | docker login --username AWS --password-stdin ${registry}

                        docker tag taskhub-api:${IMAGE_TAG} ${registry}/${ECR_API_REPO}:${IMAGE_TAG}
                        docker tag taskhub-api:${IMAGE_TAG} ${registry}/${ECR_API_REPO}:latest
                        docker tag taskhub-api:${IMAGE_TAG} ${registry}/${ECR_WORKER_REPO}:${IMAGE_TAG}
                        docker tag taskhub-api:${IMAGE_TAG} ${registry}/${ECR_WORKER_REPO}:latest

                        docker push ${registry}/${ECR_API_REPO}:${IMAGE_TAG}
                        docker push ${registry}/${ECR_API_REPO}:latest
                        docker push ${registry}/${ECR_WORKER_REPO}:${IMAGE_TAG}
                        docker push ${registry}/${ECR_WORKER_REPO}:latest
                    """
                }
            }
        }

        // =====================================================================
        // Stage 6: Deploy to ECS
        // Only runs on the main devops branch
        // =====================================================================
        stage('Deploy to ECS') {
            when {
                branch 'devops-sql-aws'
            }

            steps {
                sh """
                    aws ecs update-service \
                        --cluster ${ECS_CLUSTER} \
                        --service ${ECS_API_SERVICE} \
                        --force-new-deployment \
                        --region ${AWS_REGION}

                    aws ecs update-service \
                        --cluster ${ECS_CLUSTER} \
                        --service ${ECS_WORKER_SERVICE} \
                        --force-new-deployment \
                        --region ${AWS_REGION}

                    aws ecs wait services-stable \
                        --cluster ${ECS_CLUSTER} \
                        --services ${ECS_API_SERVICE} ${ECS_WORKER_SERVICE} \
                        --region ${AWS_REGION}
                """
            }
        }
    }

    // -------------------------------------------------------------------------
    // Post-pipeline actions
    // always  → runs regardless of result (cleanup)
    // success → runs only on green build
    // failure → runs only on red build (rollback + notify)
    // -------------------------------------------------------------------------
    post {
        always {
            echo "Pipeline finished — cleaning up local Docker images"
            sh "docker rmi taskhub-api:${IMAGE_TAG} taskhub-api:latest || true"
            cleanWs()   // clean Jenkins workspace
        }

        success {
            echo "✅ Pipeline succeeded — image ${IMAGE_TAG} deployed to ECS"
        }

        failure {
            echo "❌ Pipeline failed — check logs above"
            // In production: send Slack/email notification here
            // slackSend(color: 'danger', message: "Deploy failed: ${env.BUILD_URL}")
        }
    }
}
