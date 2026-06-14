resource "google_storage_bucket" "data_bucket" {
  name          = "${var.environment}-banking-mesh-data-${var.project_id}"
  location      = var.region
  force_destroy = true
  
  uniform_bucket_level_access = true
}

# Automatically upload all JSON files from the data/ directory to the bucket
resource "google_storage_bucket_object" "user_data" {
  for_each = fileset("${path.module}/../../../../data", "*.json")
  name     = each.value
  source   = "${path.module}/../../../../data/${each.value}"
  bucket   = google_storage_bucket.data_bucket.name
}

# Get the default compute service account
data "google_compute_default_service_account" "default" {
}

# Grant the Default Compute SA access to the Storage Bucket
resource "google_storage_bucket_iam_member" "sa_storage_admin" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}
