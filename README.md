# Google Cloud Dynamic DNS (DDNS) Updater

A lightweight, Dockerized Python script that automatically updates Google Cloud DNS 'A' records with your network's current public IP address. It is designed for minimal resource usage, security, and stability.

## Features
* **Multi-Domain Support:** Update a single domain, subdomains, or wildcard records (e.g., `example.com,*.example.com`).
* **Low Resource Footprint:** Uses HTTP session pooling and manual garbage collection to prevent memory leaks in long-running environments.
* **Secure by Default:** The Docker container runs as an unprivileged, non-root user.
* **Smart Updates:** Only pushes changes to the Google Cloud API when an actual IP address mismatch is detected.

## Prerequisites: Setting up Google Cloud

Before running the container, you need to set up a Service Account in Google Cloud to authorize the script.

### 1. Create a Service Account & Get Credentials
1. Go to **IAM & Admin > Service Accounts** in the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Service Account (e.g., `ddns-updater`).
3. Grant it the **DNS Record Set Administrator** (`roles/dns.recordSetAdmin`) role.
4. Click the three dots next to your new service account, select **Manage keys** -> **Add Key** -> **Create new key** (JSON format).
5. Download the file and save it securely on your server as `credentials.json`.

### 2. Find Your Zone Name
In Google Cloud, the "Zone Name" is the internal ID you gave the zone, *not* your actual domain name.
1. In the Google Cloud Console, navigate to **Network Services > Cloud DNS**.
2. Look at the column labeled **Zone name** (e.g., `my-domain-zone`). You will need this exact string for your environment variables.

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

Create a `docker-compose.yml` file on your server:

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

```

Run it with:

```bash
docker-compose up -d

```

### Option 2: Standard Docker Run

```bash
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

```

## Troubleshooting

You can view the logs of your running container to ensure it is correctly authenticating and updating your IP:

```bash
docker logs -f gcp-ddns-updater

```
