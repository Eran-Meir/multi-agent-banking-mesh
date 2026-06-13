#!/bin/bash
set -e

PROJECT_ID=$1
REGION="me-west1"

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <project-id>"
  exit 1
fi

echo "=========================================="
echo "🛡️  VERIFYING \$0 BILLING STATE"
echo "Project: $PROJECT_ID"
echo "=========================================="

# Check for GKE clusters
echo "Checking for active GKE Clusters..."
CLUSTERS=$(gcloud container clusters list --project="$PROJECT_ID" --format="value(name)")
if [ ! -z "$CLUSTERS" ]; then
  echo "❌ ERROR: Found active GKE Clusters: $CLUSTERS"
  echo "These will incur charges. Nuke incomplete!"
  exit 1
fi
echo "✅ No active GKE Clusters found."

# Check for Cloud Functions
echo "Checking for active Cloud Functions..."
FUNCTIONS=$(gcloud functions list --project="$PROJECT_ID" --regions="$REGION" --format="value(name)")
if [ ! -z "$FUNCTIONS" ]; then
  echo "❌ ERROR: Found active Cloud Functions: $FUNCTIONS"
  echo "These may incur charges. Nuke incomplete!"
  exit 1
fi
echo "✅ No active Cloud Functions found."

# Check for Cloud Run services
echo "Checking for active Cloud Run Services..."
RUN_SERVICES=$(gcloud run services list --project="$PROJECT_ID" --region="$REGION" --format="value(name)")
if [ ! -z "$RUN_SERVICES" ]; then
  echo "❌ ERROR: Found active Cloud Run Services: $RUN_SERVICES"
  echo "These may incur charges. Nuke incomplete!"
  exit 1
fi
echo "✅ No active Cloud Run Services found."

echo ""
echo "🎉 VERIFICATION SUCCESS: All primary billable compute resources are destroyed."
echo "💵 Assuming no manual resources were created, \$0/month baseline achieved."
echo "=========================================="
