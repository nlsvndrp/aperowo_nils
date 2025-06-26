import json

from backend.amiv_api import fetch_all_events, extract_event_fields

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

def main():

    """
    Main function to execute the extraction of all events from all possible sites.
    This function is called when the script is run directly.
    """
    extract_amiv()

if __name__ == "__main__":
    main()



