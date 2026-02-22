# =============================================================================
# infra/terraform/lambda.tf
# =============================================================================
# Event-driven Lambda function for Resume Booster
#
# Triggered by EventBridge when tasks are created
# Logs task creation events to CloudWatch
# =============================================================================

# -------------------------
# EventBridge Rule
# -------------------------
resource "aws_cloudwatch_event_rule" "task_created" {
  name        = "${local.name}-task-created"
  description = "Triggered when a task is created in TaskHub"

  event_pattern = jsonencode({
    source      = ["taskhub.api"]
    detail-type = ["TaskCreated"]
  })

  tags = {
    Name = "${local.name}-task-created-rule"
  }
}

# -------------------------
# Lambda Function
# -------------------------
resource "aws_lambda_function" "resume_booster" {
  function_name    = "${local.name}-resume-booster"
  role             = aws_iam_role.lambda_exec.arn
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  handler          = "index.handler"
  runtime          = "python3.12"
  timeout          = 30

  environment {
    variables = {
      ENV = var.env
    }
  }

  tags = {
    Name = "${local.name}-resume-booster"
  }
}

# -------------------------
# Inline Lambda Code
# -------------------------
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda_function.zip"

  source {
    content  = <<-EOF
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Resume Booster Lambda - triggered when tasks are created.

    Future enhancements:
    - Parse task description for resume keywords
    - Extract skills mentioned
    - Suggest improvements
    - Send notifications
    """
    logger.info(f"Resume Booster triggered: {json.dumps(event)}")

    detail = event.get('detail', {})
    task_id = detail.get('task_id')
    task_title = detail.get('task_title')
    owner = detail.get('owner')

    logger.info(f"Task created: ID={task_id}, Title={task_title}, Owner={owner}")

    # TODO: Add resume parsing logic here
    # - Extract keywords from task_title
    # - Analyze task description
    # - Suggest improvements

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Resume booster processed successfully',
            'task_id': task_id
        })
    }
EOF
    filename = "index.py"
  }
}

# -------------------------
# Lambda IAM Role
# -------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "${local.name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${local.name}-lambda-exec-role"
  }
}

# -------------------------
# Lambda Basic Execution Policy
# -------------------------
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# -------------------------
# EventBridge Target
# -------------------------
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.task_created.name
  target_id = "ResumeLambda"
  arn       = aws_lambda_function.resume_booster.arn
}

# -------------------------
# Lambda Permission for EventBridge
# -------------------------
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.resume_booster.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.task_created.arn
}

# -------------------------
# CloudWatch Log Group
# -------------------------
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}-resume-booster"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name}-lambda-logs"
  }
}