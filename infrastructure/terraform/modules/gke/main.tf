resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  network  = var.network_name
  subnetwork = var.subnet_name

  # Allow automated killswitch teardown
  deletion_protection = false

  # Enable Autopilot
  enable_autopilot = true

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}
