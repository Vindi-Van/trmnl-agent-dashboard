# ─── Build and deploy to Cloud Run ────────────────────────────
# Usage: .\deploy.ps1 [dev|staging|prod]

$ErrorActionPreference = "Stop"

# Load config
. "$PSScriptRoot\config.ps1" @args

$TAG = "$ENVIRONMENT-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "`n=== Deploying $SERVICE_NAME ($ENVIRONMENT) ===" -ForegroundColor Cyan

# 1. Authenticate Docker with Artifact Registry
Write-Host "-> Configuring Docker auth..."
gcloud auth configure-docker "$GCP_REGION-docker.pkg.dev" --quiet

# 2. Build the container image
Write-Host "-> Building image: ${AR_IMAGE}:${TAG}"
docker build -t "${AR_IMAGE}:${TAG}" $ProjectRoot
docker tag "${AR_IMAGE}:${TAG}" "${AR_IMAGE}:latest"

# 3. Push to Artifact Registry
Write-Host "-> Pushing image..."
docker push "${AR_IMAGE}:${TAG}"
docker push "${AR_IMAGE}:latest"

# 4. Deploy to Cloud Run
Write-Host "-> Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
    --image="${AR_IMAGE}:${TAG}" `
    --region=$GCP_REGION `
    --platform=managed `
    --min-instances=$MIN_INSTANCES `
    --max-instances=$MAX_INSTANCES `
    --memory=$MEMORY `
    --cpu=$CPU `
    --port=8080 `
    --allow-unauthenticated `
    --set-env-vars="ENVIRONMENT=$ENVIRONMENT,LOG_LEVEL=INFO,DATABASE_URL=sqlite:///data/status.db" `
    --set-secrets="AGENT_TOKENS=AGENT_TOKENS:latest,TRMNL_READ_TOKEN=TRMNL_READ_TOKEN:latest" `
    --quiet

# 5. Get the service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME `
    --region=$GCP_REGION `
    --format="value(status.url)"

Write-Host "`n=== Deployment complete ===" -ForegroundColor Green
Write-Host "  Service URL: $SERVICE_URL"
Write-Host "  Health:      $SERVICE_URL/api/v1/health"
Write-Host "  TRMNL read:  $SERVICE_URL/api/v1/trmnl/openclaw"
Write-Host "  Agent write: $SERVICE_URL/api/v1/agent-status"
