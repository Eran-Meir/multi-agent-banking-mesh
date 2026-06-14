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

module "vpc_secondary" {
  source       = "../../modules/vpc"
  network_name = "${var.environment}-banking-mesh-vpc-sec"
  region       = "europe-west3"
}

module "gke_secondary" {
  source       = "../../modules/gke"
  project_id   = var.project_id
  cluster_name = "${var.environment}-banking-mesh-gke-sec"
  region       = "europe-west3"
  network_name = module.vpc_secondary.network_name
  subnet_name  = module.vpc_secondary.subnet_name
}

module "billing" {
  source             = "../../modules/billing"
  project_id         = var.project_id
  environment        = var.environment
  # Note: You need a billing account ID for prod, using a dummy or ignoring budget for prod if not specified
  billing_account_id = "014236-1449C2-E83270"
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

module "monitoring" {
  source         = "../../modules/monitoring"
  project_id     = var.project_id
  dashboard_name = "${var.environment}-banking-mesh-dashboard"
  cluster_name   = "${var.environment}-banking-mesh-gke"
}

resource "google_compute_address" "orchestrator_ip" {
  name   = "${var.environment}-orchestrator-ip"
  region = var.region
}

resource "google_compute_address" "orchestrator_ip_secondary" {
  name   = "${var.environment}-orchestrator-ip-sec"
  region = "europe-west3"
}
