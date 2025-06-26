'''For the AMIV website, we can fetch events from the AMIV API.
This script fetches all events from the AMIV API, filters them for those containing "apero" or "food" in their title or description,
and extracts relevant information such as URL, title, date, start and end times, and location'''

# Import necessary libraries.
import requests
import urllib.parse
import json
import unicodedata

# Normalize text by removing diacritical marks (accents).
def normalize_text(text):
    """Normalize text by removing diacritical marks (accents)."""
    return ''.join(
        char for char in unicodedata.normalize('NFD', text)
        if unicodedata.category(char) != 'Mn'
    )

# Filter dictionary for the API query (on the server side).
def build_api_url(base_url, filter_dict):
    """Construct the full API URL with the 'where' query parameter."""
    query_string = urllib.parse.urlencode({"where": json.dumps(filter_dict)})
    return f"{base_url}?{query_string}"

# Filter function to check if an event contains "apero" in any of its text fields (locally).
def event_contains_apero(event):
    """Check if any of the event's text fields contain 'apero'."""
    # Combine several relevant text fields.
    fields = [
        event.get("title_en", ""),
        event.get("description_en", ""),
        event.get("catchphrase_en", ""),
        event.get("title_de", ""),
        event.get("description_de", ""),
        event.get("catchphrase_de", "")
    ]
    # Join the fields into one string, convert to lower case, and normalize.
    combined_text = normalize_text(" ".join(fields).lower())
    # Return True if "apero" is found in the combined text.
    return "apero" in combined_text

# Fetch all events from the API, handling pagination.
def fetch_all_events(base_url, filter_dict=None):
    events = []
    
    # Build the initial URL with filter if provided.
    url = build_api_url(base_url, filter_dict) if filter_dict else base_url
    
    while url:
        #print("Fetching:", url)  # Debug: print the URL of the current page.
        
        # Possibly useful to save the visited URLs to a file.
        # with open("data/visited_urls.json", "w", encoding="utf-8") as outfile:
        #     json.dump(url, outfile, ensure_ascii=False, indent=2)

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Assuming the API returns a JSON object with a '_items' key for the list of events.
        if isinstance(data, dict) and '_items' in data:
            events.extend(data['_items'])
            # Use the 'next' link if available.
            url = data.get('_links', {}).get('next', {}).get('href')
            # If the API returns a relative URL, join it with the base URL.
            if url and not url.startswith('http'):

                # Remove any trailing slashes from base_url before joining.
                url = requests.compat.urljoin(base_url.rstrip('/'), url)

        # If the API returns a list of events directly.
        # This is less common but some APIs might do this.        
        elif isinstance(data, list):
            events.extend(data)
            # Break out if it's just a list
            url = None
        else:
            url = None
    return events

# Extract specific fields from an event.
def extract_event_fields(event):
    """
    Extract specific fields from an event:
    - URL, extracted from the event's _links section
    - Title (preferring title_en over title_de)
    - Date (from time_start, in YYYY-MM-DD format)
    - Start and end times (only hh:mm)
    - Location
    """
    # Extract the URL assuming it is found in the '_links' section.
    url = event.get("_links", {}).get("self", {}).get("href", "")
    # Prefer the English title, fallback to the German title.
    title = event.get("title_en", event.get("title_de", ""))
    # Get the full start time string in ISO 8601 format.
    time_start = event.get("time_start", "")
    date = time_start[:10] if time_start else ""
    # Extract only hh:mm (characters at positions 11 to 15)
    start_time = time_start[11:16] if time_start and len(time_start) >= 16 else ""
    # Similarly extract end time in hh:mm from the provided time_end field.
    time_end = event.get("time_end", "")
    end_time = time_end[11:16] if time_end and len(time_end) >= 16 else ""
    # Get the location (if available)
    location = event.get("location", "")
    
    return {
        "url": url,
        "title": title,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "location": location
    }