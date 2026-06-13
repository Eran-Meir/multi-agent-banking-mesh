variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "me-west1"
}
variable "environment" { type = string }

variable "billing_account_id" {
  type        = string
  default     = "014236-1449C2-E83270"
  description = "Billing Account ID for alerts"
}
