terraform {
  backend "gcs" {
    bucket = "YOUR_PROJECT_ID-tfstate-prod"
    prefix = "terraform/state"
  }
}
