# Configuration Reference

## Environment Variables

### Google Cloud DNS Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes* | Path to GCP service account key file inside container | `/secrets/credentials.json` |
| `GCP_PROJECT_ID` | Yes* | Your Google Cloud project ID | `my-project-123456` |
| `GCP_ZONE_NAME` | Yes* | Internal zone name from GCP Cloud DNS (not domain name) | `my-domain-zone` |
| `GCP_DOMAIN_NAMES` | Yes* | Comma-separated list of domains to update | `example.com,*.example.com` |

*Required only if using GCP DNS updates

### Cloudflare Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CLOUDFLARE_API_TOKEN` | Yes* | Cloudflare API token with DNS edit permissions | `1234567890abcdef...` |
| `CLOUDFLARE_ZONE_ID` | Yes* | Zone ID from Cloudflare dashboard | `abcdef1234567890...` |
| `CLOUDFLARE_DOMAIN_NAMES` | Yes* | Comma-separated list of domains to update | `example.com,*.example.com` |
| `CLOUDFLARE_PROXIED` | No | Enable Cloudflare proxy (orange cloud) | `true` or `false` (default) |

*Required only if using Cloudflare DNS updates

### Global Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DNS_TTL` | No | `300` | DNS record TTL in seconds (60-86400) |
| `CHECK_INTERVAL` | No | `300` | How often to check for IP changes in seconds |

## Domain Name Format

### Google Cloud DNS

- Supports trailing dot notation (automatically added if missing)
- Examples:
  - `example.com` → becomes `example.com.`
  - `*.example.com` → becomes `*.example.com.`
  - `sub.example.com.` → stays `sub.example.com.`

### Cloudflare

- Does NOT use trailing dots (automatically removed if present)
- Examples:
  - `example.com` → stays `example.com`
  - `*.example.com` → stays `*.example.com`
  - `sub.example.com.` → becomes `sub.example.com`

## Multi-Domain Examples

### Update Multiple GCP Domains

```bash
-e GCP_DOMAIN_NAMES="example.com,*.example.com,api.example.com"
```

### Update Multiple Cloudflare Domains

```bash
-e CLOUDFLARE_DOMAIN_NAMES="example.com,app.example.com,api.example.com"
```

### Mixed Configuration

You can update different domains on different providers:

```bash
-e GCP_DOMAIN_NAMES="gcp.example.com,internal.example.com"
-e CLOUDFLARE_DOMAIN_NAMES="cf.example.com,public.example.com"
```

## Security Considerations

1. **GCP Credentials File**: Mount as read-only (`:ro`) in Docker
2. **Cloudflare API Token**: Use a token with minimal permissions (only DNS:Edit for specific zone)
3. **Environment Variables**: Consider using Docker secrets or environment files instead of command-line flags

## Advanced: Using Environment Files

Create a `.env` file:

```bash
# GCP
GCP_PROJECT_ID=your-project-id
GCP_ZONE_NAME=your-zone-name
GCP_DOMAIN_NAMES=example.com

# Cloudflare
CLOUDFLARE_API_TOKEN=your-token
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_DOMAIN_NAMES=example.com

# Global
DNS_TTL=300
CHECK_INTERVAL=300
```

Reference in docker-compose.yml:

```yaml
services:
  hybrid-ddns:
    image: weasts/gcp-ddns-updater:latest
    env_file: .env
    volumes:
      - /path/to/credentials.json:/secrets/credentials.json:ro
```
