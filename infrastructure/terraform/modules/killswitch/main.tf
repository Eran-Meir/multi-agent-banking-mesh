resource "google_secret_manager_secret" "github_pat" {
  project   = var.project_id
  secret_id = "github-pat"

  replication {
    auto {}
  }
}

resource "google_storage_bucket" "function_bucket" {
  name          = "${var.project_id}-killswitch-src"
  location      = var.region
  project       = var.project_id
  force_destroy = true
}

data "archive_file" "source" {
  type        = "zip"
  source_dir  = "../../../functions/killswitch"
  output_path = "/tmp/killswitch.zip"
}

resource "google_storage_bucket_object" "zip" {
  name   = "killswitch-${data.archive_file.source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.source.output_path
}

resource "google_cloudfunctions2_function" "killswitch" {
  name        = "billing-killswitch"
  location    = var.region
  project     = var.project_id
  description = "Triggers GitHub Actions Nuke pipeline when billing threshold is met"

  build_config {
    runtime     = "python310"
    entry_point = "killswitch"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.zip.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    environment_variables = {
      GCP_PROJECT = var.project_id
      GITHUB_REPO = var.github_repo
    }
  }

  event_trigger {
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = var.billing_topic_id
    retry_policy   = "RETRY_POLICY_DO_NOT_RETRY"
  }
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.github_pat.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_cloudfunctions2_function.killswitch.service_config[0].service_account_email}"
}
