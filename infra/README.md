# Infrastructure — Deployment Guide

## Prerequisites

- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- A GCP project with billing enabled

## Configuration

All GCP config values are read from your `.env` file (root of the repo):

```env
GCP_PROJECT=your-gcp-project-id
GCP_REGION=us-west1
AR_REPO=trmnl-agent-dashboard
SERVICE_NAME=status-board
```

## Deployment Steps

### 1. Authenticate with GCP

```powershell
gcloud auth login
```

### 2. Provision GCP Resources (one-time)

```powershell
.\infra\setup-gcp.ps1
```

This creates:
- Artifact Registry repo (Docker container storage)
- Secret Manager secrets (`AGENT_TOKENS`, `TRMNL_READ_TOKEN`)
- Enables required APIs (Cloud Run, Artifact Registry, Secret Manager)

### 3. Store Secrets

```powershell
# Agent write tokens (JSON map of token → identity)
'{"<token1>": {"agent_id": "matrim", "display_name": "Matrim Cauthon"}, ...}' | gcloud secrets versions add AGENT_TOKENS --data-file=-

# TRMNL read token
'<your-read-token>' | gcloud secrets versions add TRMNL_READ_TOKEN --data-file=-
```

Generate secure tokens with:
```powershell
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

### 4. Deploy

```powershell
.\infra\deploy.ps1
```

This builds the Docker image, pushes to Artifact Registry, and deploys to Cloud Run.
The service URL is printed at the end.

### 5. Verify

```powershell
# Health check
curl https://<your-service-url>/api/v1/health
```

## Updating Secrets

To rotate a token:
```powershell
'<new-value>' | gcloud secrets versions add AGENT_TOKENS --data-file=-
.\infra\deploy.ps1   # Redeploy to pick up new secret version
```

## Tearing Down

```powershell
.\infra\teardown.ps1
```

Deletes the Cloud Run service and container images. Secrets are preserved.

## Scripts Reference

| Script | Purpose |
|---|---|
| `config.ps1` | Shared config — reads `.env`, sets defaults |
| `setup-gcp.ps1` | One-time GCP resource provisioning |
| `deploy.ps1` | Build + push + deploy to Cloud Run |
| `teardown.ps1` | Delete service + clean up images |
