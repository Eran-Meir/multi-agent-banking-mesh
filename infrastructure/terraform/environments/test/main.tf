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
  cluster_name   = "${var.environment}-banking-mesh-gke"
}

module "billing" {
  source      = "../../modules/billing"
  project_id  = var.project_id
  environment = var.environment
}

module "killswitch" {
  source           = "../../modules/killswitch"
  project_id       = var.project_id
  region           = var.region
  environment      = var.environment
  billing_topic_id = module.billing.billing_topic_id
}

module "artifact_registry" {
  source        = "../../modules/artifact_registry"
  project_id    = var.project_id
  region        = var.region
  repository_id = "${var.environment}-banking-mesh-repo"
}

module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

resource "google_compute_address" "orchestrator_ip" {
  name   = "${var.environment}-orchestrator-ip"
  region = var.region
}
