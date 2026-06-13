# Enterprise GKE Architecture

## Infrastructure Setup
- **GCP Region**: me-west1 (Tel Aviv)
- **Cluster**: GKE Autopilot
- **Workload Identity**: Enabled for zero hardcoded secrets.

## Soft Multi-Tenancy
The cluster is divided into isolated environments via Kubernetes Namespaces:
- dev
- stress-test (Used for Chaos Engineering and HPA validation)
- prod

## Cost Controls ( Target)
Strict teardown pipelines (	erraform destroy) are enforced to ensure that infrastructure is completely removed when not actively used for demonstration, keeping costs at .
