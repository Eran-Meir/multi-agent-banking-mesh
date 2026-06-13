output "repository_id" {
  value = google_artifact_registry_repository.repo.id
}

output "repository_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}
