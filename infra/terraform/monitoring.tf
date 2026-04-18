# infra/terraform/monitoring.tf
# =============================================================================
# monitoring.tf — CloudWatch Alarms + SNS Notifications
#
# WHY ALARMS?
#   "Monitoring means knowing your system is broken before users tell you."
#
# WHAT WE MONITOR:
#   1. ECS API CPU utilization       — app is overloaded
#   2. ECS API memory utilization    — memory leak or undersized task
#   3. ALB 5xx error rate            — app is returning errors
#   4. ALB unhealthy host count      — containers failing health checks
#   5. RDS CPU utilization           — database under pressure
#   6. RDS DB connections            — connection pool exhaustion (common bug)
#
# INTERVIEW ANSWER:
#   "I set alarms on the four golden signals: latency (ALB 5xx as proxy),
#    traffic (request count), errors (5xx rate), and saturation (CPU/memory).
#    All alarms publish to SNS which sends email notifications."
# =============================================================================

# -----------------------------------------------------------------------------
# SNS topic — all alarms publish here → email notification
# -----------------------------------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name = "taskhub-${var.environment}-alerts"

  tags = {
    Name = "taskhub-${var.environment}-alerts"
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# -----------------------------------------------------------------------------
# 1. ECS API — CPU utilization
# Fires when average CPU > 80% for 5 consecutive minutes
# Action: investigate if autoscaling didn't kick in, or scale manually
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "ecs_api_cpu" {
  alarm_name          = "taskhub-${var.environment}-api-cpu-high"
  alarm_description   = "API CPU utilization exceeded 80% for 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = "taskhub-${var.environment}-cluster"
    ServiceName = "taskhub-${var.environment}-api"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-api-cpu-high" }
}

# -----------------------------------------------------------------------------
# 2. ECS API — memory utilization
# Fires when average memory > 80% for 5 minutes
# OOMKilled containers restart silently — this catches it proactively
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "ecs_api_memory" {
  alarm_name          = "taskhub-${var.environment}-api-memory-high"
  alarm_description   = "API memory utilization exceeded 80% for 5 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = "taskhub-${var.environment}-cluster"
    ServiceName = "taskhub-${var.environment}-api"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-api-memory-high" }
}

# -----------------------------------------------------------------------------
# 3. ALB — 5xx error rate
# Fires when more than 10 server errors occur in a 5-minute window
# This is the first alarm that fires during an outage
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "taskhub-${var.environment}-alb-5xx-errors"
  alarm_description   = "ALB is returning 5xx errors — application may be down"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-alb-5xx" }
}

# -----------------------------------------------------------------------------
# 4. ALB — unhealthy host count
# Fires immediately when any container fails health checks
# Most useful alarm — catches ECS task crashes before users notice
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "taskhub-${var.environment}-unhealthy-hosts"
  alarm_description   = "One or more ECS tasks are failing ALB health checks"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-unhealthy-hosts" }
}

# -----------------------------------------------------------------------------
# 5. RDS — CPU utilization
# Fires when DB CPU > 70% for 10 minutes
# Earlier threshold than ECS (70% not 80%) because DB recovery is slower
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "taskhub-${var.environment}-rds-cpu-high"
  alarm_description   = "RDS CPU exceeded 70% — check for slow queries or missing indexes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 70
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = "taskhub-${var.environment}-postgres"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-rds-cpu-high" }
}

# -----------------------------------------------------------------------------
# 6. RDS — DB connection count
# Fires when connections > 80% of max allowed
# db.t4g.micro max connections = 85
# Threshold: 68 (80% of 85)
#
# WHY THIS MATTERS:
#   ECS runs N tasks × pool_size connections each
#   Example: 4 tasks × 15 pool_size = 60 connections — already 70% of max
#   This alarm catches connection exhaustion before it causes 500 errors
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "taskhub-${var.environment}-rds-connections-high"
  alarm_description   = "RDS connection count is near the maximum — risk of pool exhaustion"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 68
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = "taskhub-${var.environment}-postgres"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
  ok_actions    = [aws_sns_topic.alerts.arn]

  tags = { Name = "taskhub-${var.environment}-rds-connections-high" }
}

# -----------------------------------------------------------------------------
# CloudWatch Dashboard — single pane of glass for all metrics
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_dashboard" "taskhub" {
  dashboard_name = "taskhub-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "ECS API — CPU & Memory"
          period = 60
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", "taskhub-${var.environment}-cluster", "ServiceName", "taskhub-${var.environment}-api"],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", "taskhub-${var.environment}-cluster", "ServiceName", "taskhub-${var.environment}-api"]
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title  = "ALB — Request Count & 5xx Errors"
          period = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix]
          ]
        }
      },
      {
        type = "metric"
        properties = {
          title  = "RDS — CPU & Connections"
          period = 60
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "taskhub-${var.environment}-postgres"],
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "taskhub-${var.environment}-postgres"]
          ]
        }
      }
    ]
  })
}
