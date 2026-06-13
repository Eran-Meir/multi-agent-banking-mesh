resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for Multi-Agent Banking Mesh"
  format        = "DOCKER"
  project       = var.project_id
}
