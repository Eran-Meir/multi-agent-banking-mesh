resource "google_pubsub_topic" "billing_alerts" {
  name    = "${var.environment}-billing-alerts-topic"
  project = var.project_id
}
