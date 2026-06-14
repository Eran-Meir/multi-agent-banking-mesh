output "bucket_name" {
  value = google_storage_bucket.data_bucket.name
}

output "workload_sa_email" {
  value = google_service_account.workload_sa.email
}
