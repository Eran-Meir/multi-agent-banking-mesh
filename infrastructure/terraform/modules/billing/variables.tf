variable "billing_account_id" {
  type        = string
  description = "The GCP Billing Account ID"
}

variable "project_id" {
  type        = string
  description = "The GCP Project ID to filter budget on"
}

variable "environment" {
  type        = string
  description = "The deployment environment (e.g. test, prod)"
}
