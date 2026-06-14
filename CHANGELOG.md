# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.5] - 2026-06-14
### Added
- Configured a dynamic Terraform Cleanup Policy for Google Artifact Registry to strictly cap storage at the 4 most recent deployments and forcefully delete all older, untagged images.
### Changed
- Refined the `README.md` Mermaid diagrams to explicitly model the Artifact Registry ingestion paths, Regional Load Balancer isolations, and accurate HPA replica thresholds (1-4).

## [v1.0.4] - 2026-06-14
### Changed
- Refactored CI/CD pipeline naming and execution flow to perfectly match the requested sequential workflow order (1-6).
- Nested and merged the Stress Test and Manual App Test into a single, unified `2. App Test` workflow with interactive checkboxes for streamlined validation.

## [v1.0.3] - 2026-06-14
### Changed
- Enforced strict Coding Guidelines by removing all "magic numbers" (hardcoded loops and load simulations) across the Orchestrator API and GitHub Actions workflows, replacing them with explicit Configuration Constants.
- Injected the physical Kubernetes datacenter `REGION` directly into the Orchestrator's API response for enhanced multi-region traffic visibility.

## [v1.0.2] - 2026-06-14
### Added
- Added `pod_id` to the Orchestrator API payload to expose underlying Kubernetes routing metrics.
- Created `4. Manual App Test` GitHub Action to manually barrage the LoadBalancers and mathematically prove traffic distribution across the HPA replicas.

## [v1.0.1] - 2026-06-14
### Changed
- Updated Orchestrator root endpoint to return an Enterprise welcome greeting instead of "Hello World".
- Integrated automated `App Tester` step into CI/CD pipelines to assert 200 OK and expected API payload across all regional endpoints.

## [v1.0.0] - 2026-06-14
### Added
- Multi-Region Active-Active Production Environment (europe-west4, europe-west3).
- Test Environment (me-west1) with isolated dashboard and autoscaling bounds.
- Orchestrator Agent API Gateway baseline.
- Automated GitHub Actions deployment pipelines for Test and Prod.
- GKE Autopilot clusters, VPC networks, and Artifact Registries.
- MQL-based monitoring dashboard for multi-region GKE pod scaling.
- Automated $9.00/mo Cloud Billing Killswitch using Cloud Functions and Pub/Sub.
