output "orchestrator_external_ip" {
  description = "The static external IP address of the Orchestrator service."
  value       = google_compute_address.orchestrator_ip.address
}
