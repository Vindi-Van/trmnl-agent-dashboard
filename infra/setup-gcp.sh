#!/usr/bin/env bash
# ─── Provision GCP resources for the Status Board ─────────────
# Usage: ./setup-gcp.sh [dev|staging|prod]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh" "${1:-dev}"

echo "=== Setting up GCP resources for ${ENVIRONMENT} ==="

# 1. Set project
echo "→ Setting project..."
gcloud config set project "${GCP_PROJECT}"

# 2. Enable required APIs
echo "→ Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

# 3. Create Artifact Registry repo (if not exists)
echo "→ Creating Artifact Registry repo..."
gcloud artifacts repositories describe "${AR_REPO}" \
  --location="${GCP_REGION}" 2>/dev/null || \
gcloud artifacts repositories create "${AR_REPO}" \
  --repository-format=docker \
  --location="${GCP_REGION}" \
  --description="TRMNL Agent Dashboard containers" \
  --quiet

# 4. Create secrets (if not exist)
echo "→ Creating secrets..."
for SECRET in AGENT_TOKENS TRMNL_READ_TOKEN; do
  gcloud secrets describe "${SECRET}" 2>/dev/null || \
  gcloud secrets create "${SECRET}" \
    --replication-policy="automatic" \
    --quiet
  echo "  ✓ ${SECRET}"
done

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Set secret values:"
echo "     echo '<value>' | gcloud secrets versions add AGENT_TOKENS --data-file=-"
echo "     echo '<value>' | gcloud secrets versions add TRMNL_READ_TOKEN --data-file=-"
echo "  2. Run: ./infra/deploy.sh ${ENVIRONMENT}"
