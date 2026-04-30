# Troubleshooting Guide

## Common Issues

### Container Fails to Start

**Check logs:**
```bash
docker logs hybrid-ddns-updater
```

**Common causes:**
- Missing required environment variables
- Invalid GCP credentials file path
- Invalid Cloudflare API token or Zone ID

### GCP Authentication Errors

**Error:** `Failed to initialize GCP DNS client`

**Solutions:**
1. Verify credentials file exists and is mounted correctly:
   ```bash
   docker exec hybrid-ddns-updater ls -la /secrets/credentials.json
   ```

2. Check service account has correct permissions (DNS Record Set Administrator role)

3. Ensure Cloud DNS API is enabled in your GCP project

4. Verify `GCP_ZONE_NAME` is the internal zone name, not your domain name

### Cloudflare API Errors

**Error:** `Cloudflare API returned error`

**Solutions:**
1. Verify API token has correct permissions (Edit zone DNS)
2. Check Zone ID is correct (from Cloudflare dashboard Overview page)
3. Ensure domain exists in your Cloudflare account

### IP Not Updating

**Check public IP detection:**
```bash
docker exec hybrid-ddns-updater curl -s https://api.ipify.org
```

**Common causes:**
- Network connectivity issues
- Firewall blocking outbound HTTPS requests
- ipify.org service unavailable (rare)

### Domains Not Updating

**Check configured domains:**
```bash
docker logs hybrid-ddns-updater | grep "configured"
```

**Verify:**
- Domain names are correctly formatted
- GCP domains end with dot (automatic)
- Cloudflare domains don't end with dot (automatic)

## Debug Mode

To see more detailed logs, you can modify the logging level in `dynamic_dns.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

Then rebuild the image.

## Testing Without Docker

You can test the script directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID="your-project"
export GCP_ZONE_NAME="your-zone"
export GCP_DOMAIN_NAMES="example.com"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Run
python3 dynamic_dns.py
```

## FAQ

**Q: Can I use both GCP and Cloudflare?**
A: Yes! Configure both sets of environment variables.

**Q: How often does it check for IP changes?**
A: Default is every 300 seconds (5 minutes). Change with `CHECK_INTERVAL`.

**Q: Will it update if the IP hasn't changed?**
A: No, it only updates when a mismatch is detected.

**Q: Can I run multiple containers for different domains?**
A: Yes, just use different container names and configurations.

**Q: Where are logs stored?**
A: Logs go to stdout/stderr and can be viewed with `docker logs`.

## Getting Help

If you're still having issues:
1. Check the [GitHub Issues](https://github.com/PrestonWest87/HomelabDNSUpdater/issues)
2. Create a new issue with:
   - Your docker-compose.yml (remove sensitive data)
   - Full container logs
   - Description of the problem
