#!/bin/bash
# Multi-Agent Banking System - GCP Bootstrap Script
# This script sets up the GCS bucket for Terraform state and configures
# Workload Identity Federation for secretless GitHub Actions CI/CD.

set -e

# ==========================================
# CONFIGURATION
# ==========================================
# Replace these with your actual values
PROJECT_ID="erx-agent-bank-core-dev-01"
GITHUB_REPO="Eran-Meir/multi-agent-banking-mesh" # e.g., username/repo
REGION="me-west1"

# Automatically generated values based on project ID
TF_STATE_BUCKET="${PROJECT_ID}-tf-state"
SA_NAME="github-actions-tf"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"

echo "=========================================="
echo "Bootstrapping GCP Project: $PROJECT_ID"
echo "=========================================="

# 1. Set the active project
gcloud config set project "$PROJECT_ID"

# 2. Enable necessary APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  compute.googleapis.com \
  container.googleapis.com \
  monitoring.googleapis.com

# 3. Create GCS Bucket for Terraform State
echo "Checking/Creating GCS Bucket for Terraform state: gs://$TF_STATE_BUCKET"
if ! gsutil ls "gs://${TF_STATE_BUCKET}" >/dev/null 2>&1; then
  gsutil mb -l "$REGION" "gs://${TF_STATE_BUCKET}"
  gsutil versioning set on "gs://${TF_STATE_BUCKET}"
  echo "Bucket created."
else
  echo "Bucket already exists."
fi

# 4. Create Service Account for GitHub Actions
echo "Creating Service Account: $SA_NAME"
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions Terraform SA" || true

# Grant Editor and Project IAM Admin roles to the SA so it can manage infrastructure
echo "Granting roles to Service Account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/resourcemanager.projectIamAdmin"

# 5. Create Workload Identity Pool
echo "Creating Workload Identity Pool: $POOL_NAME"
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --location="global" \
  --display-name="GitHub Actions Pool" || true

POOL_ID=$(gcloud iam workload-identity-pools describe "$POOL_NAME" \
  --location="global" \
  --format="value(name)")

# 6. Create Workload Identity Provider
echo "Creating Workload Identity Provider: $PROVIDER_NAME"
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com" || true

# 7. Bind the GitHub Repository to the Service Account
echo "Binding GitHub Repository ($GITHUB_REPO) to the Service Account..."
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository/${GITHUB_REPO}"

# 8. Output configuration for GitHub Secrets/Variables
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --format="value(name)")

echo ""
echo "=========================================="
echo "BOOTSTRAP COMPLETE!"
echo "=========================================="
echo "Please add the following as Repository Variables in your GitHub Repo:"
echo ""
echo "1. GCP_PROJECT_ID             = $PROJECT_ID"
echo "2. GCP_TF_STATE_BUCKET        = $TF_STATE_BUCKET"
echo "3. WORKLOAD_IDENTITY_PROVIDER = $PROVIDER_ID"
echo "4. SERVICE_ACCOUNT_EMAIL      = $SA_EMAIL"
echo "=========================================="
