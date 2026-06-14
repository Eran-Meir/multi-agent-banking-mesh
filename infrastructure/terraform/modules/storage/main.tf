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

# Create a Google Service Account for Workload Identity
resource "google_service_account" "workload_sa" {
  account_id   = "${var.environment}-mesh-sa"
  display_name = "Banking Mesh Workload Service Account"
}

# Grant the GSA access to the Storage Bucket
resource "google_storage_bucket_iam_member" "sa_storage_admin" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.workload_sa.email}"
}

# Bind the GSA to the KSA (Kubernetes Service Account) via Workload Identity
resource "google_service_account_iam_binding" "workload_identity_binding" {
  service_account_id = google_service_account.workload_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[default/banking-mesh-ksa]"
  ]
}
