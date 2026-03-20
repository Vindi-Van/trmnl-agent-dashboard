# ─── Provision GCP resources for the Status Board ─────────────
# Usage: .\setup-gcp.ps1 [dev|staging|prod]

# Suppress PowerShell's stderr-as-error behavior for gcloud
$ErrorActionPreference = "SilentlyContinue"

# Load config
. "$PSScriptRoot\config.ps1" @args

Write-Host "`n=== Setting up GCP resources for $ENVIRONMENT ===" -ForegroundColor Cyan

# Helper: run gcloud without PowerShell capturing stderr as errors
function Invoke-Gcloud {
    param([string]$Arguments)
    $output = cmd /c "gcloud $Arguments 2>&1"
    return @{ ExitCode = $LASTEXITCODE; Output = $output }
}

# 1. Set project
Write-Host "-> Setting project..."
$r = Invoke-Gcloud "config set project $GCP_PROJECT"
if ($r.ExitCode -ne 0) {
    Write-Host "  ! Failed to set project. Run 'gcloud auth login' first." -ForegroundColor Red
    exit 1
}
Write-Host "  + Project set to $GCP_PROJECT" -ForegroundColor Green

# 2. Enable required APIs
Write-Host "-> Enabling APIs..."
$r = Invoke-Gcloud "services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --quiet"
if ($r.ExitCode -ne 0) {
    Write-Host "  ! Failed to enable APIs." -ForegroundColor Red
    Write-Host $r.Output
    exit 1
}
Write-Host "  + APIs enabled" -ForegroundColor Green

# 3. Create Artifact Registry repo (if not exists)
Write-Host "-> Creating Artifact Registry repo..."
$r = Invoke-Gcloud "artifacts repositories describe $AR_REPO --location=$GCP_REGION"
if ($r.ExitCode -ne 0) {
    $r = Invoke-Gcloud "artifacts repositories create $AR_REPO --repository-format=docker --location=$GCP_REGION --description=`"TRMNL Agent Dashboard containers`" --quiet"
    if ($r.ExitCode -ne 0) {
        Write-Host "  ! Failed to create Artifact Registry repo." -ForegroundColor Red
        Write-Host $r.Output
        exit 1
    }
    Write-Host "  + Repo created" -ForegroundColor Green
} else {
    Write-Host "  = Repo already exists" -ForegroundColor Yellow
}

# 4. Create secrets (if not exist)
Write-Host "-> Creating secrets..."
foreach ($secret in @("AGENT_TOKENS", "TRMNL_READ_TOKEN")) {
    $r = Invoke-Gcloud "secrets describe $secret"
    if ($r.ExitCode -ne 0) {
        $r = Invoke-Gcloud "secrets create $secret --replication-policy=automatic --quiet"
        if ($r.ExitCode -ne 0) {
            Write-Host "  ! Failed to create secret: $secret" -ForegroundColor Red
            Write-Host $r.Output
            exit 1
        }
        Write-Host "  + $secret created" -ForegroundColor Green
    } else {
        Write-Host "  = $secret already exists" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Set secret values:"
Write-Host "     echo '<value>' | gcloud secrets versions add AGENT_TOKENS --data-file=-"
Write-Host "     echo '<value>' | gcloud secrets versions add TRMNL_READ_TOKEN --data-file=-"
Write-Host "  2. Run: .\infra\deploy.ps1 $ENVIRONMENT"
