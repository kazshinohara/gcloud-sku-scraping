import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin
import logging
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://cloud.google.com/skus/sku-groups"
OUTPUT_FILE = "sku_id_to_group_mapping.csv"
TEMP_DIR = "temp_data"
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_WORKERS = 5  # Limit concurrent requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def make_request(url, retries=MAX_RETRIES):
    """Make an HTTP request with retry logic."""
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Too many requests
                wait_time = RETRY_DELAY * (2 ** i) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {i+1}/{retries}")
                time.sleep(wait_time)
            else:
                logger.warning(f"Failed to fetch {url}. Status code: {response.status_code}. Retry {i+1}/{retries}")
                time.sleep(RETRY_DELAY)
        except (requests.RequestException, ConnectionError) as e:
            logger.warning(f"Request error for {url}: {str(e)}. Retry {i+1}/{retries}")
            time.sleep(RETRY_DELAY)
    
    logger.error(f"Failed to fetch {url} after {retries} retries")
    return None

def get_sku_group_links():
    """Extract all SKU group links from the main page."""
    logger.info(f"Fetching SKU group links from {BASE_URL}")
    
    response = make_request(BASE_URL)
    if not response:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all links that look like SKU group links
    sku_group_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'skus/sku-groups/' in href and href != BASE_URL:
            full_url = urljoin("https://cloud.google.com", href)
            sku_group_name = link.text.strip()
            if sku_group_name:  # Only add if the link has text content
                sku_group_links.append((sku_group_name, full_url))
    
    logger.info(f"Found {len(sku_group_links)} SKU group links")
    return sku_group_links

def extract_sku_ids(url, sku_group_name):
    """Extract SKU IDs from a specific SKU group page."""
    logger.info(f"Processing SKU group: {sku_group_name}")
    
    response = make_request(url)
    if not response:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    sku_ids = []
    # Look for tables that might contain SKU IDs
    tables = soup.find_all('table')
    for table in tables:
        # Check for header row to determine which column contains SKU IDs
        headers = [header.text.strip().lower() for header in table.find_all('th')]
        sku_id_col_index = None
        
        # Common headers for SKU ID columns
        sku_header_variants = ['sku id', 'sku', 'id', 'sku code']
        
        for variant in sku_header_variants:
            if variant in headers:
                sku_id_col_index = headers.index(variant)
                break
        
        # If we couldn't identify the SKU ID column, assume it's the first column
        if sku_id_col_index is None:
            sku_id_col_index = 0
            
        # Extract SKU IDs from the determined column
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if cells and len(cells) > sku_id_col_index:
                potential_sku_id = cells[sku_id_col_index].text.strip()
                # SKU IDs typically follow a pattern like alphanumeric characters and hyphens
                if potential_sku_id and re.match(r'^[A-Z0-9][A-Z0-9-]+$', potential_sku_id):
                    # Skip header-like values
                    if potential_sku_id.lower() not in ['sku id', 'sku', 'id', 'sku code']:
                        sku_ids.append(potential_sku_id)
    
    # Check for pagination
    pagination_links = soup.select('a[aria-label*="page"]') or soup.select('a.pagination')
    for link in pagination_links:
        if 'href' in link.attrs:
            next_page_url = urljoin(url, link['href'])
            if next_page_url != url:  # Prevent infinite loop
                logger.info(f"Found pagination link, processing next page: {next_page_url}")
                # Add a small delay before fetching the next page
                time.sleep(random.uniform(1, 2))
                response = make_request(next_page_url)
                if response:
                    next_soup = BeautifulSoup(response.text, 'html.parser')
                    for table in next_soup.find_all('table'):
                        for row in table.find_all('tr'):
                            cells = row.find_all('td')
                            if cells and len(cells) > 0:
                                potential_sku_id = cells[0].text.strip()
                                if potential_sku_id and re.match(r'^[A-Z0-9][A-Z0-9-]+$', potential_sku_id):
                                    if potential_sku_id.lower() not in ['sku id', 'sku', 'id', 'sku code']:
                                        sku_ids.append(potential_sku_id)
    
    # Remove duplicates while preserving order
    unique_sku_ids = []
    for sku_id in sku_ids:
        if sku_id not in unique_sku_ids:
            unique_sku_ids.append(sku_id)
    
    logger.info(f"Found {len(unique_sku_ids)} SKU IDs for {sku_group_name}")
    return [(sku_id, sku_group_name) for sku_id in unique_sku_ids]

def process_sku_group(sku_group_data):
    """Process a single SKU group with exponential backoff."""
    sku_group_name, url = sku_group_data
    try:
        # Add jitter to prevent thundering herd problem
        time.sleep(random.uniform(0.5, 1.5))
        return extract_sku_ids(url, sku_group_name)
    except Exception as e:
        logger.error(f"Error processing {sku_group_name}: {str(e)}")
        return []

def save_checkpoint(data, filename="checkpoint.csv"):
    """Save current progress to a checkpoint file."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    checkpoint_path = os.path.join(TEMP_DIR, filename)
    
    with open(checkpoint_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['SKU ID', 'SKU Group'])
        writer.writerows(data)
    
    logger.info(f"Checkpoint saved: {len(data)} SKU IDs saved to {checkpoint_path}")

def main():
    """Main function to extract SKU IDs and write to CSV."""
    logger.info("Starting the SKU ID extraction process")
    
    # Create temp directory for checkpoints
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Get all SKU group links
    sku_group_links = get_sku_group_links()
    if not sku_group_links:
        logger.error("No SKU group links found. Exiting.")
        return
    
    # Process SKU groups concurrently with a thread pool
    all_sku_data = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_sku_group = {executor.submit(process_sku_group, group_data): group_data for group_data in sku_group_links}
        completed = 0
        
        for future in as_completed(future_to_sku_group):
            sku_data = future.result()
            all_sku_data.extend(sku_data)
            completed += 1
            
            # Save checkpoint every 10 SKU groups processed
            if completed % 10 == 0:
                save_checkpoint(all_sku_data, f"checkpoint_{completed}.csv")
                logger.info(f"Progress: {completed}/{len(sku_group_links)} SKU groups processed")
    
    # Write final results to CSV
    logger.info(f"Writing {len(all_sku_data)} SKU IDs to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['SKU ID', 'SKU Group'])
        writer.writerows(all_sku_data)
    
    logger.info("Process completed successfully")

if __name__ == "__main__":
    main() 