# Release v1.0.0: Hybrid GCP + Cloudflare DDNS Updater

## Features
- Add Cloudflare DNS support alongside Google Cloud DNS
- Multi-provider support (update both providers simultaneously)
- Comprehensive documentation added (INSTALLATION, CONFIGURATION, TROUBLESHOOTING)
- Smart updates: only push changes when IP mismatch detected

## Docker Image
```bash
docker pull weasts/gcp-ddns-updater:v1.0.0
```

**Docker Hub:** https://hub.docker.com/repository/docker/weasts/gcp-ddns-updater

## Installation
See the [README.md](https://github.com/PrestonWest87/HomelabDNSUpdater/blob/main/README.md) for installation instructions.

## What's Changed
- Updated README to reflect hybrid GCP + Cloudflare support
- Added documentation in `docs/` folder
- Built and pushed Docker images to Docker Hub
- Tagged release v1.0.0
