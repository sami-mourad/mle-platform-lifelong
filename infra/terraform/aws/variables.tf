variable "project" {
  type        = string
  default     = "mle-platform"
  description = "Resource-name prefix."
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment."
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "database_username" {
  type      = string
  default   = "mle"
  sensitive = true
}

variable "database_password" {
  type      = string
  sensitive = true
  validation {
    condition     = length(var.database_password) >= 16
    error_message = "database_password must contain at least 16 characters."
  }
}
