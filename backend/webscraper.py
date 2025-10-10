"""Web scraping utilities for collecting 'apero' events.

This module crawls the given URLs and searches for occurrences of the
word 'apero' (or 'aperitif') in the HTML content. When a match is
found, it attempts to extract event details such as date, time and
location. Results are stored in ``apero_results.json``.

The crawler keeps a record of already visited URLs in
``visited_urls.json`` so that subsequent runs only fetch new pages.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterable, Set, Tuple

import requests
from bs4 import BeautifulSoup
import urllib.parse

# List of websites to crawl for apero events. Feel free to extend this.
URLS: Iterable[str] = [
    "https://vseth.ethz.ch/events/",
]

# Files used to persist crawl results/state.
DATA_DIR = Path(__file__).resolve().parent
VISITED_FILE = DATA_DIR / "visited_urls.json"
OUTPUT_FILE = DATA_DIR / "apero_results.json"

# Use a custom user agent to be polite when requesting pages.
HEADERS = {
    "User-Agent": "AperoBot/1.0 (+https://example.com/bot)"
}

# Storage for discovered apero events during a crawl session.
found_apero: list[dict[str, str]] = []

def load_visited(filename: Path) -> Set[str]:
    """Return a set of URLs previously visited.

    Parameters
    ----------
    filename : Path
        JSON file containing a list of URLs.
    """
    try:
        with filename.open("r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        # No state yet; start fresh.
        return set()
    except Exception as exc:  # pragma: no cover - best effort
        print(f"Could not load visited URLs from {filename}: {exc}")
        return set()

def save_visited(filename: Path, visited: Set[str]) -> None:
    """Persist the set of visited URLs as a JSON list."""
    try:
        with filename.open("w", encoding="utf-8") as f:
            json.dump(sorted(visited), f, indent=2)
    except Exception as exc:  # pragma: no cover - best effort
        print(f"Could not save visited URLs to {filename}: {exc}")

def extract_event_details(soup: BeautifulSoup) -> Tuple[str, str, str, str]:
    """Extract event date, start time, end time and location from the page.

    The logic is heuristic: it first looks for ``<time>`` elements, then
    for classes such as ``location`` or ``venue``. If those are missing it
    scans the entire text for common keywords.
    """
    date = "Not found"
    start_time = "Not found"
    end_time = "Not found"
    location = "Not found"

    full_text = soup.get_text("|", strip=True)

    # Look for ISO-style or textual date/time information in <time> tags.
    time_el = soup.find("time")
    if time_el:
        text = time_el.get_text(strip=True)
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        time_match = re.search(r"(\d{1,2}:\d{2})", text)
        if date_match:
            date = date_match.group(1)
        if time_match:
            start_time = time_match.group(1)

    # Attempt to find location via common classes.
    loc_el = soup.find(class_="location") or soup.find(class_="venue")
    if loc_el:
        location = loc_el.get_text(strip=True)
    else:
        loc_match = re.search(r"(?:Venue|Location)[:\-]\s*([A-Za-z0-9 ,.-]+)", full_text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()

    return date, start_time, end_time, location

def crawl(url: str, domain: str, visited: Set[str], depth: int = 0, max_depth: int = 3) -> None:
    """Recursively crawl ``url`` and its subpages.

    Parameters
    ----------
    url : str
        The starting URL.
    domain : str
        Domain that links must match to be followed. This prevents the
        crawler from wandering off to other sites.
    visited : set[str]
        Set of URLs already fetched.
    depth : int, default ``0``
        Current recursion depth.
    max_depth : int, default ``3``
        Maximum recursion depth allowed.
    """
    if url in visited:
        return
    visited.add(url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except Exception as exc:
        print(f"Error fetching {url}: {exc}")
        return

    if resp.status_code != 200:
        print(f"Skipping {url} due to status code {resp.status_code}")
        return

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "No title"

    # Look for 'apero' or 'aperitif' case-insensitively.
    if re.search(r"apero|aperitif", html, re.IGNORECASE):
        date, start_t, end_t, location = extract_event_details(soup)
        snippet_match = re.search(r".{0,100}(apero|aperitif).{0,100}", html, re.IGNORECASE)
        snippet = snippet_match.group(0) if snippet_match else "Snippet not available"
        found_apero.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "date": date,
            "start_time": start_t,
            "end_time": end_t,
            "location": location,
        })
        print(f"Found 'apero' in: {url}")

    # Follow links on the page within the same domain.
    for link in soup.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        absolute = urllib.parse.urljoin(url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.netloc != domain:
            continue
        if any(absolute.lower().endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png", ".gif"]):
            continue
        if absolute not in visited and depth < max_depth:
            time.sleep(1)  # be polite
            crawl(absolute, domain, visited, depth + 1, max_depth)

def main() -> None:
    """Entry point used when executing this module as a script."""
    for start in URLS:
        print(f"Starting crawl from: {start}")
        visited = load_visited(VISITED_FILE)
        domain = urllib.parse.urlparse(start).netloc
        crawl(start, domain, visited)
        save_visited(VISITED_FILE, visited)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(found_apero, f, indent=2, ensure_ascii=False)

    print(f"Apero data saved to {OUTPUT_FILE}")

if __name__ == "__main__":  # pragma: no cover
    main()
