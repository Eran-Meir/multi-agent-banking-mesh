resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for Multi-Agent Banking Mesh"
  format        = "DOCKER"
  project       = var.project_id

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-recent-4"
    action = "KEEP"
    most_recent_versions {
      keep_count = 4
    }
  }

  cleanup_policies {
    id     = "delete-older-than-1-hour"
    action = "DELETE"
    condition {
      older_than = "3600s"
    }
  }
}
