resource "google_pubsub_topic" "billing_alerts" {
  name    = "billing-alerts-topic"
  project = var.project_id
}

resource "google_billing_budget" "budget" {
  billing_account = var.billing_account_id
  display_name    = "Budget Alert Multi-Agent Bank"

  budget_filter {
    projects = ["projects/$${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "9"
    }
  }

  # Alert when spend hits 100%
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  # Send JSON notifications to our Pub/Sub topic
  all_updates_rule {
    pubsub_topic   = google_pubsub_topic.billing_alerts.id
    schema_version = "1.0"
  }
}
