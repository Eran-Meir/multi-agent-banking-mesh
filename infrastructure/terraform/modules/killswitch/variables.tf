variable "project_id" { type = string }
variable "region" { type = string }
variable "billing_topic_id" { type = string }
variable "github_repo" {
  type    = string
  default = "Eran-Meir/multi-agent-banking-mesh"
}
variable "environment" { type = string }
