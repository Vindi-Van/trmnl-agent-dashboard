#!/usr/bin/env bash
# ─── Build and deploy to Cloud Run ────────────────────────────
# Usage: ./deploy.sh [dev|staging|prod]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh" "${1:-dev}"

PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
TAG="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

echo "=== Deploying ${SERVICE_NAME} (${ENVIRONMENT}) ==="

# 1. Authenticate Docker with Artifact Registry
echo "→ Configuring Docker auth..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

# 2. Build the container image
echo "→ Building image: ${AR_IMAGE}:${TAG}"
docker build -t "${AR_IMAGE}:${TAG}" "${PROJECT_ROOT}"
docker tag "${AR_IMAGE}:${TAG}" "${AR_IMAGE}:latest"

# 3. Push to Artifact Registry
echo "→ Pushing image..."
docker push "${AR_IMAGE}:${TAG}"
docker push "${AR_IMAGE}:latest"

# 4. Deploy to Cloud Run
echo "→ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${AR_IMAGE}:${TAG}" \
  --region="${GCP_REGION}" \
  --platform=managed \
  --min-instances="${MIN_INSTANCES}" \
  --max-instances="${MAX_INSTANCES}" \
  --memory="${MEMORY}" \
  --cpu="${CPU}" \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=${ENVIRONMENT},LOG_LEVEL=INFO,DATABASE_URL=sqlite:///data/status.db" \
  --set-secrets="AGENT_TOKENS=AGENT_TOKENS:latest,TRMNL_READ_TOKEN=TRMNL_READ_TOKEN:latest" \
  --quiet

# 5. Get the service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --format="value(status.url)")

echo ""
echo "=== Deployment complete ==="
echo "  Service URL: ${SERVICE_URL}"
echo "  Health:      ${SERVICE_URL}/api/v1/health"
echo "  TRMNL read:  ${SERVICE_URL}/api/v1/trmnl/openclaw"
echo "  Agent write: ${SERVICE_URL}/api/v1/agent-status"
