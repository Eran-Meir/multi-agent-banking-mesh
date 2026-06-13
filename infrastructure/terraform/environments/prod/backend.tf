terraform {
  backend "gcs" {
    bucket = "erx-agent-bank-core-dev-01-tf-state"
    prefix = "terraform/state/prod"
  }
}
