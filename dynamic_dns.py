import os
import sys
import time
import requests
import logging
import gc

try:
    from google.cloud import dns
    from google.api_core import exceptions
except ImportError:
    pass  # Handled below if GCP domains are provided

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Configuration ---
# GCP Specific
GCP_RAW_DOMAINS = os.getenv('GCP_DOMAIN_NAMES') or os.getenv('GCP_DOMAIN_NAME')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
GCP_ZONE_NAME = os.getenv('GCP_ZONE_NAME')

# Cloudflare Specific
CF_RAW_DOMAINS = os.getenv('CLOUDFLARE_DOMAIN_NAMES')
CF_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CF_ZONE_ID = os.getenv('CLOUDFLARE_ZONE_ID')
CF_PROXIED = os.getenv('CLOUDFLARE_PROXIED', 'false').lower() == 'true'

try:
    TTL = int(os.getenv('DNS_TTL', 300))
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
except ValueError:
    logging.critical("DNS_TTL and CHECK_INTERVAL must be integers.")
    sys.exit(1)

IP_SERVICE_URL = 'https://api.ipify.org'
RECORD_TYPE = 'A'

# --- Validate Configuration & Parse Domains ---
GCP_DOMAINS = []
CF_DOMAINS = []

if GCP_RAW_DOMAINS:
    if not all([GCP_PROJECT_ID, GCP_ZONE_NAME]):
        logging.critical("Error: GCP_DOMAIN_NAMES provided, but missing GCP_PROJECT_ID or GCP_ZONE_NAME")
        sys.exit(1)
    # GCP requires trailing dots
    GCP_DOMAINS = [d.strip() + '.' if not d.strip().endswith('.') else d.strip() for d in GCP_RAW_DOMAINS.split(',')]

if CF_RAW_DOMAINS:
    if not all([CF_API_TOKEN, CF_ZONE_ID]):
        logging.critical("Error: CLOUDFLARE_DOMAIN_NAMES provided, but missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ZONE_ID")
        sys.exit(1)
    # Cloudflare strictly does not use trailing dots
    CF_DOMAINS = [d.strip().rstrip('.') for d in CF_RAW_DOMAINS.split(',')]

if not GCP_DOMAINS and not CF_DOMAINS:
    logging.critical("Error: No domains configured. Please set GCP_DOMAIN_NAMES and/or CLOUDFLARE_DOMAIN_NAMES.")
    sys.exit(1)

http_session = requests.Session()

def get_public_ip() -> str | None:
    try:
        response = http_session.get(IP_SERVICE_URL, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not get public IP: {e}")
        return None

# --- GCP Functions ---
def get_gcp_record(zone, domain_name):
    try:
        records = zone.list_resource_record_sets()
        for record in records:
            if record.name == domain_name and record.record_type == RECORD_TYPE:
                return record
        return None
    except exceptions.GoogleAPICallError as e:
        logging.error(f"Could not get GCP DNS record for {domain_name}: {e}")
        return None

def update_gcp_record(zone, old_record, new_public_ip: str, domain_name: str):
    try:
        changes = zone.changes()
        if old_record:
            changes.delete_record_set(old_record)
        new_record = zone.resource_record_set(domain_name, RECORD_TYPE, TTL, [new_public_ip])
        changes.add_record_set(new_record)
        changes.create()
        
        timeout = time.time() + 60 
        while changes.status != 'done':
            if time.time() > timeout:
                logging.error(f"Timeout waiting for GCP DNS change on {domain_name} to complete.")
                break
            time.sleep(5)
            changes.reload()
        logging.info(f"Successfully updated GCP DNS for {domain_name} to {new_public_ip}")
    except exceptions.GoogleAPICallError as e:
        logging.error(f"Failed to update GCP DNS record for {domain_name}: {e}")

# --- Cloudflare Functions ---
def get_cf_headers():
    return {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }

def get_cf_record(domain_name):
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records?name={domain_name}&type={RECORD_TYPE}"
    try:
        response = http_session.get(url, headers=get_cf_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['success'] and len(data['result']) > 0:
            return data['result'][0]
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not get Cloudflare DNS record for {domain_name}: {e}")
        return None

def update_cf_record(old_record, new_public_ip: str, domain_name: str):
    data = {
        "type": RECORD_TYPE,
        "name": domain_name,
        "content": new_public_ip,
        "ttl": TTL,
        "proxied": CF_PROXIED
    }
    try:
        if old_record:
            # Update existing
            url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{old_record['id']}"
            response = http_session.put(url, headers=get_cf_headers(), json=data, timeout=10)
        else:
            # Create new
            url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"
            response = http_session.post(url, headers=get_cf_headers(), json=data, timeout=10)
            
        response.raise_for_status()
        result = response.json()
        if result.get('success'):
            logging.info(f"Successfully updated Cloudflare DNS for {domain_name} to {new_public_ip}")
        else:
            logging.error(f"Cloudflare API returned error for {domain_name}: {result.get('errors')}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update Cloudflare DNS record for {domain_name}: {e}")

# --- Main Logic ---
def main():
    logging.info(f"--- Dynamic DNS Updater Started ---")
    if GCP_DOMAINS:
        logging.info(f"GCP Domains configured: {len(GCP_DOMAINS)}")
    if CF_DOMAINS:
        logging.info(f"Cloudflare Domains configured: {len(CF_DOMAINS)}")
    
    # Initialize GCP if needed
    gcp_zone = None
    if GCP_DOMAINS:
        try:
            dns_client = dns.Client(project=GCP_PROJECT_ID)
            gcp_zone = dns_client.zone(GCP_ZONE_NAME)
            gcp_zone.reload()
            logging.info(f"Successfully connected to GCP DNS zone '{GCP_ZONE_NAME}'.")
        except Exception as e:
            logging.critical(f"Failed to initialize GCP DNS client: {e}")
            sys.exit(1)

    while True:
        try:
            public_ip = get_public_ip()
            if public_ip is None:
                logging.warning("Skipping check due to failure in getting public IP.")
            else:
                # --- Process GCP Domains ---
                for domain in GCP_DOMAINS:
                    old_record = get_gcp_record(gcp_zone, domain)
                    dns_ip = old_record.rrdatas[0] if old_record and old_record.rrdatas else None
                    
                    if dns_ip == public_ip:
                        logging.info(f"[GCP: {domain}] IP addresses match ({public_ip}). No update needed.")
                    else:
                        logging.warning(f"[GCP: {domain}] IP mismatch! Public: {public_ip}, DNS: {dns_ip}. Updating...")
                        update_gcp_record(gcp_zone, old_record, public_ip, domain)
                        
                # --- Process Cloudflare Domains ---
                for domain in CF_DOMAINS:
                    old_record = get_cf_record(domain)
                    dns_ip = old_record['content'] if old_record else None
                    
                    if dns_ip == public_ip:
                        logging.info(f"[CF: {domain}] IP addresses match ({public_ip}). No update needed.")
                    else:
                        logging.warning(f"[CF: {domain}] IP mismatch! Public: {public_ip}, DNS: {dns_ip}. Updating...")
                        update_cf_record(old_record, public_ip, domain)

        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}")
        
        gc.collect()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
