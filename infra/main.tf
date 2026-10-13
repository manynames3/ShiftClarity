terraform {
  required_version = ">= 1.14"
  backend "s3" {}
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
provider "aws" {
  region = var.region
  default_tags { tags = { Product = "ShiftClarity", Environment = "synthetic-pilot" } }
}
variable "region" { default = "us-east-1" }
variable "name" { default = "shiftclarity-synthetic" }
variable "org_id" { default = "synthetic-pilot" }
locals {
  app_origin = aws_apigatewayv2_api.pilot.api_endpoint
}
variable "image_identifier" {
  type        = string
  description = "Previously reviewed ECR image URI pinned to a sha256 digest."
  validation {
    condition     = can(regex("@sha256:[a-f0-9]{64}$", var.image_identifier))
    error_message = "An immutable ECR image digest is required."
  }
}
variable "database_secret_arn" {
  type        = string
  description = "Existing Secrets Manager secret holding a restricted PostgreSQL URL with sslmode=verify-full."
}
variable "monthly_budget_usd" {
  default     = "5"
  description = "Visibility budget; this does not cap spending or verify promotional credits."
}

resource "aws_s3_bucket" "private" {
  bucket_prefix = var.name
  force_destroy = false
  lifecycle { prevent_destroy = true }
}
resource "aws_s3_bucket_public_access_block" "private" {
  bucket                  = aws_s3_bucket.private.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_ownership_controls" "private" {
  bucket = aws_s3_bucket.private.id
  rule { object_ownership = "BucketOwnerEnforced" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "private" {
  bucket = aws_s3_bucket.private.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "tls" {
  bucket = aws_s3_bucket.private.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect    = "Deny", Principal = "*", Action = "s3:*",
    Resource  = [aws_s3_bucket.private.arn, "${aws_s3_bucket.private.arn}/*"],
    Condition = { Bool = { "aws:SecureTransport" = "false" } }
  }] })
}
resource "aws_s3_bucket_lifecycle_configuration" "retention" {
  bucket = aws_s3_bucket.private.id
  rule {
    id     = "quarantine-expiry"
    status = "Enabled"
    filter { prefix = "${var.org_id}/quarantine/" }
    expiration { days = 1 }
  }
  rule {
    id     = "accepted-source-expiry"
    status = "Enabled"
    filter { prefix = "${var.org_id}/accepted/" }
    expiration { days = 30 }
  }
}
resource "aws_cognito_user_pool" "pilot" {
  name              = var.name
  mfa_configuration = "ON"
  software_token_mfa_configuration { enabled = true }
  admin_create_user_config { allow_admin_create_user_only = true }
  password_policy {
    minimum_length                   = 14
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 3
  }
  user_pool_tier = "LITE"
  account_recovery_setting {
    recovery_mechanism {
      name     = "admin_only"
      priority = 1
    }
  }
  deletion_protection = "ACTIVE"
  lifecycle { prevent_destroy = true }
}
resource "aws_cognito_user_pool_client" "web" {
  name                                 = "shiftclarity-web"
  user_pool_id                         = aws_cognito_user_pool.pilot.id
  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["${local.app_origin}/auth/callback"]
  logout_urls                          = ["${local.app_origin}/pilot/", "${local.app_origin}/auth/continue"]
  prevent_user_existence_errors        = "ENABLED"
  enable_token_revocation              = true
  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"]
  auth_session_validity                = 3
  access_token_validity                = 15
  id_token_validity                    = 15
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}
resource "aws_cognito_user_pool_domain" "pilot" {
  domain       = var.name
  user_pool_id = aws_cognito_user_pool.pilot.id
}
resource "aws_cognito_user_pool_ui_customization" "pilot" {
  user_pool_id = aws_cognito_user_pool.pilot.id
  client_id    = aws_cognito_user_pool_client.web.id
  image_file   = filebase64("${path.module}/shiftclarity-login.png")
  css          = <<-CSS
    .banner-customizable { background-color: #ffffff; }
    .label-customizable { font-weight: 600; color: #142333; }
    .textDescription-customizable { color: #142333; }
    .submitButton-customizable { background-color: #006C78; color: #ffffff; }
    .submitButton-customizable:hover { background-color: #005963; }
  CSS
  depends_on   = [aws_cognito_user_pool_domain.pilot]
}
resource "aws_iam_role" "runtime" {
  name_prefix = "${var.name}-"
  assume_role_policy = jsonencode({ Version = "2012-10-17", Statement = [{
    Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole"
  }] })
}
resource "aws_iam_role_policy" "runtime" {
  role = aws_iam_role.runtime.id
  policy = jsonencode({ Version = "2012-10-17", Statement = [
    { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
    Resource = ["${aws_s3_bucket.private.arn}/${var.org_id}/*"] },
    { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [var.database_secret_arn] },
    { Effect = "Allow", Action = ["cognito-idp:GetUserPoolMfaConfig", "cognito-idp:DescribeUserPoolClient", "cognito-idp:AdminGetUser", "cognito-idp:AdminSetUserMFAPreference"],
    Resource = [aws_cognito_user_pool.pilot.arn] },
    { Effect = "Allow", Action = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
    Resource = [aws_sqs_queue.jobs.arn] },
    { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"],
    Resource = ["${aws_cloudwatch_log_group.web.arn}:*", "${aws_cloudwatch_log_group.worker.arn}:*"] }
  ] })
}

resource "aws_sqs_queue" "dead" {
  name                      = "${var.name}-dead.fifo"
  fifo_queue                = true
  sqs_managed_sse_enabled   = true
  message_retention_seconds = 1209600
}
resource "aws_sqs_queue" "jobs" {
  name                       = "${var.name}-jobs.fifo"
  fifo_queue                 = true
  sqs_managed_sse_enabled    = true
  visibility_timeout_seconds = 180
  message_retention_seconds  = 345600
  redrive_policy             = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dead.arn, maxReceiveCount = 5 })
}
resource "aws_cloudwatch_log_group" "web" {
  name              = "/aws/lambda/${var.name}-web"
  retention_in_days = 7
}
resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${var.name}-worker"
  retention_in_days = 7
}
locals {
  runtime_environment = {
    APP_ORIGIN              = local.app_origin
    ORG_ID                  = var.org_id
    PRIVATE_BUCKET          = aws_s3_bucket.private.id
    COGNITO_POOL_ID         = aws_cognito_user_pool.pilot.id
    OIDC_ISSUER             = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.pilot.id}"
    OIDC_CLIENT_ID          = aws_cognito_user_pool_client.web.id
    DATABASE_SECRET_ARN     = var.database_secret_arn
    JOB_QUEUE_URL           = aws_sqs_queue.jobs.url
    JOB_QUEUE_ARN           = aws_sqs_queue.jobs.arn
    PYTHONDONTWRITEBYTECODE = "1"
  }
}
resource "aws_lambda_function" "web" {
  function_name = "${var.name}-web"
  role          = aws_iam_role.runtime.arn
  package_type  = "Image"
  image_uri     = var.image_identifier
  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = 29
  environment { variables = local.runtime_environment }
  image_config { command = ["backend.lambda_handler.web"] }
  depends_on = [aws_iam_role_policy.runtime, aws_cloudwatch_log_group.web]
}
resource "aws_lambda_function" "worker" {
  function_name = "${var.name}-worker"
  role          = aws_iam_role.runtime.arn
  package_type  = "Image"
  image_uri     = var.image_identifier
  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = 30
  environment { variables = local.runtime_environment }
  image_config { command = ["backend.lambda_handler.worker"] }
  depends_on = [aws_iam_role_policy.runtime, aws_cloudwatch_log_group.worker]
}
resource "aws_lambda_event_source_mapping" "jobs" {
  event_source_arn        = aws_sqs_queue.jobs.arn
  function_name           = aws_lambda_function.worker.arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
}
resource "aws_apigatewayv2_api" "pilot" {
  name          = var.name
  protocol_type = "HTTP"
}
resource "aws_apigatewayv2_integration" "web" {
  api_id                 = aws_apigatewayv2_api.pilot.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.web.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}
resource "aws_apigatewayv2_route" "web" {
  api_id    = aws_apigatewayv2_api.pilot.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.web.id}"
}
resource "aws_apigatewayv2_stage" "pilot" {
  api_id      = aws_apigatewayv2_api.pilot.id
  name        = "$default"
  auto_deploy = true
  default_route_settings {
    throttling_burst_limit = 60
    throttling_rate_limit  = 10
  }
}
resource "aws_lambda_permission" "gateway" {
  statement_id  = "shiftclarity-http-api"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.web.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.pilot.execution_arn}/*"
}
resource "aws_budgets_budget" "pilot" {
  name         = var.name
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
}
resource "aws_cloudwatch_metric_alarm" "queue_dead_letters" {
  alarm_name          = "${var.name}-dead-letters"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  dimensions          = { QueueName = aws_sqs_queue.dead.name }
}
output "cognito_pool" { value = aws_cognito_user_pool.pilot.id }
output "cognito_client" { value = aws_cognito_user_pool_client.web.id }
output "app_origin" { value = local.app_origin }
output "private_bucket" { value = aws_s3_bucket.private.id }
output "job_queue" { value = aws_sqs_queue.jobs.url }
output "job_queue_arn" { value = aws_sqs_queue.jobs.arn }
output "dead_queue" { value = aws_sqs_queue.dead.url }
