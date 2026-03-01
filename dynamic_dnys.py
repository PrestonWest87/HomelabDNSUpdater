import os
import sys
import time
import requests
import logging
import gc
from google.cloud import dns
from google.api_core import exceptions

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- Configuration ---
PROJECT_ID = os.getenv('GCP_PROJECT_ID')
ZONE_NAME = os.getenv('GCP_ZONE_NAME')
RAW_DOMAIN_NAMES = os.getenv('GCP_DOMAIN_NAME')

try:
    TTL = int(os.getenv('DNS_TTL', 300))
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
except ValueError:
    logging.critical("DNS_TTL and CHECK_INTERVAL must be integers.")
    sys.exit(1)

IP_SERVICE_URL = 'https://api.ipify.org'
RECORD_TYPE = 'A'

# --- Validate Configuration ---
if not all([PROJECT_ID, ZONE_NAME, RAW_DOMAIN_NAMES]):
    missing_vars = [k for k, v in {'GCP_PROJECT_ID': PROJECT_ID, 'GCP_ZONE_NAME': ZONE_NAME, 'GCP_DOMAIN_NAME': RAW_DOMAIN_NAMES}.items() if not v]
    logging.critical(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Parse multiple domains and ensure they all have a trailing dot
DOMAIN_NAMES = []
for d in RAW_DOMAIN_NAMES.split(','):
    d = d.strip()
    if not d.endswith('.'):
        d += '.'
    DOMAIN_NAMES.append(d)

http_session = requests.Session()

def get_public_ip() -> str | None:
    try:
        response = http_session.get(IP_SERVICE_URL, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not get public IP: {e}")
        return None

def get_dns_record(zone, domain_name):
    try:
        records = zone.list_resource_record_sets()
        for record in records:
            if record.name == domain_name and record.record_type == RECORD_TYPE:
                return record
        logging.warning(f"No '{RECORD_TYPE}' record found for {domain_name}")
        return None
    except exceptions.GoogleAPICallError as e:
        logging.error(f"Could not get DNS record for {domain_name}: {e}")
        return None

def update_dns_record(zone, old_record, new_public_ip: str, domain_name: str):
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
                logging.error(f"Timeout waiting for DNS change on {domain_name} to complete.")
                break
            logging.info(f"Waiting for DNS change on {domain_name} to complete (status: {changes.status})...")
            time.sleep(5)
            changes.reload()
        logging.info(f"Successfully updated DNS for {domain_name} to {new_public_ip}")
    except exceptions.GoogleAPICallError as e:
        logging.error(f"Failed to update DNS record for {domain_name}: {e}")

def main():
    logging.info(f"--- Dynamic DNS Updater Started for {len(DOMAIN_NAMES)} domain(s) ---")
    try:
        dns_client = dns.Client(project=PROJECT_ID)
        zone = dns_client.zone(ZONE_NAME)
        zone.reload()
        logging.info(f"Successfully connected to DNS zone '{ZONE_NAME}'.")
    except exceptions.NotFound:
        logging.critical(f"DNS zone '{ZONE_NAME}' not found. Please check configuration.")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Failed to initialize Google Cloud DNS client: {e}")
        sys.exit(1)

    while True:
        try:
            public_ip = get_public_ip()
            if public_ip is None:
                logging.warning("Skipping check due to failure in getting public IP.")
            else:
                for domain in DOMAIN_NAMES:
                    old_record = get_dns_record(zone, domain)
                    dns_ip = old_record.rrdatas[0] if old_record and old_record.rrdatas else None

                    if dns_ip == public_ip:
                        logging.info(f"[{domain}] IP addresses match ({public_ip}). No update needed.")
                    else:
                        logging.warning(f"[{domain}] IP mismatch! Public IP: {public_ip}, DNS IP: {dns_ip}. Updating...")
                        update_dns_record(zone, old_record, public_ip, domain)
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}")
        
        gc.collect()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()