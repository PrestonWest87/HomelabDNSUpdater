# Google Cloud Dynamic DNS (DDNS) Updater

A lightweight, Dockerized Python script that automatically updates Google Cloud DNS 'A' records with your network's current public IP address. It is designed for minimal resource usage, security, and stability.

## Features
* **Multi-Domain Support:** Update a single domain, subdomains, or wildcard records (e.g., `example.com,*.example.com`).
* **Low Resource Footprint:** Uses HTTP session pooling and manual garbage collection to prevent memory leaks in long-running environments.
* **Secure by Default:** The Docker container runs as an unprivileged, non-root user.
* **Smart Updates:** Only pushes changes to Google Cloud API when an actual IP address mismatch is detected.

## Prerequisites

Before running the container, you need to set up a Service Account in Google Cloud:
1. Go to **IAM & Admin > Service Accounts** in the Google Cloud Console.
2. Create a new Service Account (e.g., `ddns-updater`).
3. Grant it the **DNS Record Set Administrator** (`roles/dns.recordSetAdmin`) role.
4. Create and download a new JSON key for this service account.
5. Save the file as `credentials.json` on your server.

## Environment Variables

| Variable | Description | Default | Example |
| :--- | :--- | :--- | :--- |
| `GCP_PROJECT_ID` | **(Required)** Your Google Cloud Project ID. | None | `my-gcp-project-123` |
| `GCP_ZONE_NAME` | **(Required)** The internal name of your Cloud DNS zone. | None | `my-domain-zone` |
| `GCP_DOMAIN_NAME` | **(Required)** Comma-separated list of domains to update. | None | `example.com,*.example.com` |
| `DNS_TTL` | Time-to-Live for the DNS record (in seconds). | `300` | `300` |
| `CHECK_INTERVAL`| How often to check for public IP changes (in seconds). | `300` | `300` |

## Deployment

### Option 1: Docker Compose (Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  gcp-ddns:
    image: yourdockerhubusername/gcp-ddns-updater:latest
    container_name: gcp-ddns-updater
    restart: unless-stopped
    volumes:
      # Map your downloaded GCP JSON key to the container
      - /path/to/your/credentials.json:/secrets/credentials.json:ro
    environment:
      - GCP_PROJECT_ID=your-project-id
      - GCP_ZONE_NAME=your-zone-name
      - GCP_DOMAIN_NAME=example.com,*.example.com
      - DNS_TTL=300
      - CHECK_INTERVAL=300


Run it with: docker-compose up -d
Option 2: Docker Run

```Bash

docker run -d \
  --name gcp-ddns-updater \
  --restart unless-stopped \
  -v /path/to/your/credentials.json:/secrets/credentials.json:ro \
  -e GCP_PROJECT_ID="your-project-id" \
  -e GCP_ZONE_NAME="your-zone-name" \
  -e GCP_DOMAIN_NAME="example.com,*.example.com" \
  -e DNS_TTL="300" \
  -e CHECK_INTERVAL="300" \
  yourdockerhubusername/gcp-ddns-updater:latest