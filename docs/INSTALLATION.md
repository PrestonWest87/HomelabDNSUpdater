# Installation Guide

## Prerequisites

- Docker installed on your system
- For Google Cloud DNS: A GCP project with Cloud DNS API enabled
- For Cloudflare: A Cloudflare account with API token

## Quick Start

### 1. Clone or Download

```bash
git clone https://github.com/PrestonWest87/HomelabDNSUpdater.git
cd HomelabDNSUpdater
```

### 2. Build the Docker Image (Optional)

If you want to build locally:

```bash
docker build -t hybrid-ddns-updater .
```

### 3. Prepare Your Credentials

#### Google Cloud Users

1. Download your service account JSON key file
2. Save it as `credentials.json` in a secure location on your server
3. Note the file path (e.g., `/home/user/credentials.json`)

#### Cloudflare Users

1. Generate an API token with **Edit zone DNS** permissions
2. Note down your token and Zone ID

### 4. Choose Your Deployment Method

See [docker-compose.yml example](#docker-compose-example) or [Docker Run](#docker-run) below.

## Docker Compose Example

Create a `docker-compose.yml` file:

```yaml
services:
  hybrid-ddns:
    image: weasts/gcp-ddns-updater:latest
    container_name: hybrid-ddns-updater
    restart: unless-stopped
    volumes:
      - /path/to/your/credentials.json:/secrets/credentials.json:ro
    environment:
      # -- GCP Configuration (optional) --
      - GOOGLE_APPLICATION_CREDENTIALS=/secrets/credentials.json
      - GCP_PROJECT_ID=your-gcp-project-id
      - GCP_ZONE_NAME=your-gcp-zone
      - GCP_DOMAIN_NAMES=example.com,*.example.com
      
      # -- Cloudflare Configuration (optional) --
      - CLOUDFLARE_DOMAIN_NAMES=cf.example.com
      - CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
      - CLOUDFLARE_ZONE_ID=your-cloudflare-zone-id
      - CLOUDFLARE_PROXIED=false
      
      # -- Global Settings --
      - DNS_TTL=300
      - CHECK_INTERVAL=300
```

Start with:

```bash
docker-compose up -d
```

## Docker Run

### GCP Only

```bash
docker run -d \
  --name hybrid-ddns-updater \
  --restart unless-stopped \
  -v /path/to/your/credentials.json:/secrets/credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/credentials.json \
  -e GCP_PROJECT_ID="your-project-id" \
  -e GCP_ZONE_NAME="your-zone-name" \
  -e GCP_DOMAIN_NAMES="example.com,*.example.com" \
  -e DNS_TTL="300" \
  -e CHECK_INTERVAL="300" \
  weasts/gcp-ddns-updater:latest
```

### Cloudflare Only

```bash
docker run -d \
  --name hybrid-ddns-updater \
  --restart unless-stopped \
  -e CLOUDFLARE_API_TOKEN="your-api-token" \
  -e CLOUDFLARE_ZONE_ID="your-zone-id" \
  -e CLOUDFLARE_DOMAIN_NAMES="example.com,*.example.com" \
  -e CLOUDFLARE_PROXIED="false" \
  -e DNS_TTL="300" \
  -e CHECK_INTERVAL="300" \
  weasts/gcp-ddns-updater:latest
```

### Both Providers

```bash
docker run -d \
  --name hybrid-ddns-updater \
  --restart unless-stopped \
  -v /path/to/your/credentials.json:/secrets/credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/credentials.json \
  -e GCP_PROJECT_ID="your-project-id" \
  -e GCP_ZONE_NAME="your-zone-name" \
  -e GCP_DOMAIN_NAMES="gcp.example.com" \
  -e CLOUDFLARE_API_TOKEN="your-api-token" \
  -e CLOUDFLARE_ZONE_ID="your-zone-id" \
  -e CLOUDFLARE_DOMAIN_NAMES="cf.example.com" \
  -e CLOUDFLARE_PROXIED="false" \
  -e DNS_TTL="300" \
  -e CHECK_INTERVAL="300" \
  weasts/gcp-ddns-updater:latest
```

## Verification

Check the logs to ensure everything is working:

```bash
docker logs -f hybrid-ddns-updater
```

You should see output similar to:

```
2024-01-15 10:00:00 - INFO - --- Dynamic DNS Updater Started ---
2024-01-15 10:00:00 - INFO - GCP Domains configured: 1
2024-01-15 10:00:00 - INFO - Cloudflare Domains configured: 1
2024-01-15 10:00:00 - INFO - Successfully connected to GCP DNS zone 'my-zone'.
2024-01-15 10:00:01 - INFO - [GCP: example.com.] IP addresses match (1.2.3.4). No update needed.
2024-01-15 10:00:01 - INFO - [CF: example.com] IP addresses match (1.2.3.4). No update needed.
```
