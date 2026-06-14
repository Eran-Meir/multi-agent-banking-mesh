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

# NOTE: The Google Service Account (test-mesh-sa), the bucket IAM policy,
# and the workload_identity_binding are all managed manually by the user 
# in Cloud Shell because the GitHub Actions pipeline lacks the necessary 
# IAM admin permissions.
