# ─── Tear down GCP resources ─────────────────────────────────
# Usage: .\teardown.ps1 [dev|staging|prod]
# WARNING: This deletes the Cloud Run service and associated resources.

$ErrorActionPreference = "Stop"

# Load config
. "$PSScriptRoot\config.ps1" @args

Write-Host "`n=== Tearing down $SERVICE_NAME ($ENVIRONMENT) ===" -ForegroundColor Red
$confirm = Read-Host "WARNING: This will delete the Cloud Run service. Continue? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Aborted."
    exit 0
}

# 1. Delete Cloud Run service
Write-Host "-> Deleting Cloud Run service..."
try {
    gcloud run services delete $SERVICE_NAME --region=$GCP_REGION --quiet
    Write-Host "  + Service deleted" -ForegroundColor Green
} catch {
    Write-Host "  ! Service not found" -ForegroundColor Yellow
}

# 2. Delete container images
Write-Host "-> Cleaning up container images..."
try {
    $digests = gcloud artifacts docker images list $AR_IMAGE --format="value(DIGEST)" 2>&1
    foreach ($digest in $digests) {
        if ($digest) {
            gcloud artifacts docker images delete "${AR_IMAGE}@${digest}" --quiet 2>$null
        }
    }
    Write-Host "  + Images cleaned" -ForegroundColor Green
} catch {
    Write-Host "  ! No images found" -ForegroundColor Yellow
}

Write-Host "`n=== Teardown complete ===" -ForegroundColor Green
Write-Host "Note: Secrets (AGENT_TOKENS, TRMNL_READ_TOKEN) were NOT deleted."
Write-Host "  To delete: gcloud secrets delete <NAME>"
