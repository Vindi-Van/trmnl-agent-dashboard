#!/usr/bin/env bash
# ─── GCP project and deployment configuration ────────────────
# Reads values from .env file or environment variables.
# Source this file in other infra scripts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# Load .env if it exists
if [ -f "${PROJECT_ROOT}/.env" ]; then
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
fi

# GCP project (from .env or environment)
export GCP_PROJECT="${GCP_PROJECT:?GCP_PROJECT not set — add it to .env}"
export GCP_REGION="${GCP_REGION:-us-central1}"

# Artifact Registry
export AR_REPO="${AR_REPO:-trmnl-agent-dashboard}"
export AR_IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${AR_REPO}/status-board"

# Cloud Run
export SERVICE_NAME="${SERVICE_NAME:-status-board}"
export MIN_INSTANCES="${MIN_INSTANCES:-1}"
export MAX_INSTANCES="${MAX_INSTANCES:-2}"
export MEMORY="${MEMORY:-256Mi}"
export CPU="${CPU:-1}"

# Environment (dev/staging/prod)
export ENVIRONMENT="${1:-${ENVIRONMENT:-dev}}"

echo "Config loaded: project=${GCP_PROJECT} region=${GCP_REGION} env=${ENVIRONMENT}"
