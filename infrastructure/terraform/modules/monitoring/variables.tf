variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "dashboard_name" {
  type        = string
  description = "Name of the monitoring dashboard"
}

variable "cluster_name" {
  type        = string
  description = "Name of the GKE cluster to filter metrics"
}
