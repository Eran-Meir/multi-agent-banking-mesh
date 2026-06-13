resource "google_pubsub_topic" "billing_alerts" {
  name    = "billing-alerts-topic"
  project = var.project_id
}
