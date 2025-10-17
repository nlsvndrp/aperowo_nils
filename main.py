import json
from pathlib import Path
import logging

from backend.amiv_api import fetch_all_events, extract_event_fields
from backend.scraper import (
    StructuredResearchScraper,
    load_domain_configs,
    write_jsonl,
    publish_snapshot,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_amiv():
    """
    Fetches events from the AMIV API, filters for 'apero' or 'food',
    and saves the results to a JSON file.
    """
    api = 'https://api.amiv.ethz.ch/events/'

    # Fetch all events from the AMIV API and filter them for "apero".
    events_with_apero_amiv = fetch_all_events(api, {"$or": [
    {"title_en": {"$regex": "aper", "$options": "i"}},
    {"description_en": {"$regex": "aper", "$options": "i"}},
    {"catchphrase_en": {"$regex": "aper", "$options": "i"}},
    {"title_de": {"$regex": "aper", "$options": "i"}},
    {"description_de": {"$regex": "aper", "$options": "i"}},
    {"catchphrase_de": {"$regex": "aper", "$options": "i"}},
    {"title_en": {"$regex": "food", "$options": "i"}},
    {"description_en": {"$regex": "food", "$options": "i"}},
    {"catchphrase_en": {"$regex": "food", "$options": "i"}},
    {"title_de": {"$regex": "essen", "$options": "i"}},
    {"description_de": {"$regex": "essen", "$options": "i"}},
    {"catchphrase_de": {"$regex": "essen", "$options": "i"}}
    ]})

    print(f"Found {len(events_with_apero_amiv)} events with 'apero' or 'food' in the title or description on the AMIV website.")

    # Extract specific fields from each event.
    filtered_events_amiv = [extract_event_fields(event) for event in events_with_apero_amiv]
    
    # Write the filtered events to a JSON file.
    with open("data/apero_results_amiv.json", "w", encoding="utf-8") as outfile:
        json.dump(filtered_events_amiv, outfile, ensure_ascii=False, indent=2)

    print(f"Extracted information for {len(filtered_events_amiv)} AMIV events and saved to apero_results_amiv.json.")

def run_scraper():
    """
    Runs the web scraper to find events from various domains,
    and saves the results to JSONL and a final JSON snapshot.
    """
    logger.info("Starting scraper...")
    out_jsonl_path = Path("data/aperos.jsonl")
    publish_json_path = Path("data/aperos.json")
    free_food_threshold = 0.8

    # Ensure the data directory exists
    out_jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    # It's good practice to start with clean files for each run
    if out_jsonl_path.exists():
        out_jsonl_path.unlink()
    if publish_json_path.exists():
        publish_json_path.unlink()

    domains = load_domain_configs(None)
    scraper = StructuredResearchScraper(domains)

    logger.info("Scraping across %d domains.", len(domains))
    events = scraper.run() or []
    logger.info("Scraper returned %d events.", len(events))

    if not events:
        logger.info("No events found by the scraper.")
        return

    write_jsonl(events, out_jsonl_path)
    logger.info(f"Appended {getattr(write_jsonl, '_last_count', len(events))} raw events to {out_jsonl_path}")

    publish_snapshot(events, publish_json_path, free_food_threshold)
    curated_count = getattr(publish_snapshot, '_last_count', 0)
    if curated_count > 0:
        logger.info(
            f"Wrote {curated_count} curated events to {publish_json_path} (threshold {free_food_threshold:.2f})"
        )
    else:
        logger.info(f"No events met the threshold of {free_food_threshold} to be published.")

def main():

    """
    Main function to execute the extraction of all events from all possible sites.
    This function is called when the script is run directly.
    """
    extract_amiv()
    run_scraper()


if __name__ == "__main__":
    main()