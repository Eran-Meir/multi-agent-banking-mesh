terraform {
  backend "gcs" {
    bucket = "YOUR_PROJECT_ID-tfstate-test"
    prefix = "terraform/state"
  }
}
