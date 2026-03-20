#!/usr/bin/env bash
# ─── Tear down GCP resources ─────────────────────────────────
# Usage: ./teardown.sh [dev|staging|prod]
# WARNING: This deletes the Cloud Run service and associated resources.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh" "${1:-dev}"

echo "=== Tearing down ${SERVICE_NAME} (${ENVIRONMENT}) ==="
echo "WARNING: This will delete the Cloud Run service."
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# 1. Delete Cloud Run service
echo "→ Deleting Cloud Run service..."
gcloud run services delete "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --quiet 2>/dev/null && echo "  ✓ Service deleted" || echo "  ⚠ Service not found"

# 2. Delete container images (optional)
echo "→ Cleaning up container images..."
gcloud artifacts docker images list "${AR_IMAGE}" \
  --format="value(DIGEST)" 2>/dev/null | \
while read -r digest; do
  gcloud artifacts docker images delete "${AR_IMAGE}@${digest}" --quiet 2>/dev/null
done
echo "  ✓ Images cleaned"

echo ""
echo "=== Teardown complete ==="
echo "Note: Secrets (AGENT_TOKENS, TRMNL_READ_TOKEN) were NOT deleted."
echo "  To delete secrets: gcloud secrets delete <NAME>"
