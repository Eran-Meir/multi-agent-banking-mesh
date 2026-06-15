# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.2.0] - 2026-06-15
### Added
- **Persistent User Memory**: The Orchestrator now intercepts chat interaction summaries and persists them to Google Cloud Storage. The Profiler dynamically reads these `past_interactions` to inject multi-session awareness into the user's psychological profile.
- **Executive Bank Analyst Endpoint**: Added `/analyst/chat` endpoint to query an aggregated `global_trends.json` database. The Bank Analyst AI dynamically answers high-level metric questions based on live, cross-pod platform traffic.
### Changed
- **Zero-Downtime Deployment Architecture**: Enforced strict `RollingUpdate` strategies (`maxUnavailable: 0`) and robust HTTP Readiness and Liveness Probes across all Kubernetes Deployments.
- **Smart Profiler Caching**: Engineered a fast-path cache mechanism. The Profiler dynamically invalidates and regenerates its deep Agentic Inference evaluations if the user exceeds 5 interactions or if the cache is older than 30 days.
- Swapped all ADK Agents across Orchestrator and Profiler to `gemini-3.1-flash-lite` to capitalize on the 500 Requests-Per-Day free tier allowance.
- Increased Orchestrator timeout boundaries from 5s to 30s to gracefully accommodate slow-path deep Gemini inferences.
### Fixed
- Injected a critically missing `storage` Terraform module into the `prod` infrastructure configuration to prevent user-data bucket provisioning failures.

## [v2.1.0] - 2026-06-14
### Changed
- **Major Architectural Pivot:** Ripped out raw `google-genai` manual API chaining. Migrated the Orchestrator and Profiler to **Google ADK 2.0** (`google-adk`).
- The Orchestrator now uses ADK's native intent routing graph to direct traffic to downstream pods without messy manual LLM parsing.
- The Profiler now uses an ADK `Agent` to read the sharded JSON database and execute Agentic Inference on user behavioral data.

## [v2.0.0] - 2026-06-14
### Added
- Appended an "Ephemeral Storage Usage per Pod" widget to the Terraform monitoring module to strictly monitor AI agent disk consumption within the GKE Autopilot constraints.

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
