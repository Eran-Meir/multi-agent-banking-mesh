provider "google" {
  project = var.project_id
  region  = var.region
}

module "vpc" {
  source       = "../../modules/vpc"
  network_name = "${var.environment}-banking-mesh-vpc"
  region       = var.region
}

module "gke" {
  source       = "../../modules/gke"
  project_id   = var.project_id
  cluster_name = "${var.environment}-banking-mesh-gke"
  region       = var.region
  network_name = module.vpc.network_name
  subnet_name  = module.vpc.subnet_name
}

module "monitoring" {
  source         = "../../modules/monitoring"
  project_id     = var.project_id
  dashboard_name = "${var.environment}-banking-mesh-dashboard"
}

module "billing" {
  source             = "../../modules/billing"
  project_id         = var.project_id
  billing_account_id = var.billing_account_id
}

module "killswitch" {
  source           = "../../modules/killswitch"
  project_id       = var.project_id
  region           = var.region
  billing_topic_id = module.billing.billing_topic_id
}

