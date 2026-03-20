# ─── GCP project and deployment configuration ────────────────
# Reads values from .env file. Dot-source this in other scripts:
#   . "$PSScriptRoot\config.ps1"

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent

# Load .env if it exists
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+?)\s*$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], "Process")
        }
    }
}

# GCP project (from .env or environment)
$script:GCP_PROJECT = $env:GCP_PROJECT
if (-not $script:GCP_PROJECT) {
    Write-Error "GCP_PROJECT not set - add it to .env"
    exit 1
}

$script:GCP_REGION   = if ($env:GCP_REGION)   { $env:GCP_REGION }   else { "us-central1" }
$script:AR_REPO      = if ($env:AR_REPO)      { $env:AR_REPO }      else { "trmnl-agent-dashboard" }
$script:SERVICE_NAME = if ($env:SERVICE_NAME)  { $env:SERVICE_NAME } else { "status-board" }
$script:MIN_INSTANCES = if ($env:MIN_INSTANCES) { $env:MIN_INSTANCES } else { "1" }
$script:MAX_INSTANCES = if ($env:MAX_INSTANCES) { $env:MAX_INSTANCES } else { "2" }
$script:MEMORY       = if ($env:MEMORY)        { $env:MEMORY }       else { "256Mi" }
$script:CPU          = if ($env:CPU)           { $env:CPU }          else { "1" }
$script:ENVIRONMENT  = if ($args[0])           { $args[0] }         else {
    if ($env:ENVIRONMENT) { $env:ENVIRONMENT } else { "dev" }
}

$script:AR_IMAGE = "$($script:GCP_REGION)-docker.pkg.dev/$($script:GCP_PROJECT)/$($script:AR_REPO)/status-board"

Write-Host "Config loaded: project=$($script:GCP_PROJECT) region=$($script:GCP_REGION) env=$($script:ENVIRONMENT)"
