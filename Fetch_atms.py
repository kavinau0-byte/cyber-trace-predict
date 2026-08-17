import requests
import time
import csv
import sys

# Central Bengaluru bounding box (south, west, north, east)
# Covers MG Road, Koramangala, Indiranagar, Whitefield-ish core area
BBOX = "12.90,77.55,13.05,77.70"

OVERPASS_SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

HEADERS = {
    "User-Agent": "SIH2026-CyberTracePredict/1.0 (student project, contact: kavinsihteam2026@gmail.com)"
}

QUERY = f"""
[out:json][timeout:60];
node["amenity"="atm"]({BBOX});
out body;
"""

def fetch_atms():
    for server in OVERPASS_SERVERS:
        for attempt in range(3):
            try:
                print(f"Trying {server} (attempt {attempt+1})...")
                resp = requests.post(server, data={"data": QUERY}, headers=HEADERS, timeout=90)
                resp.raise_for_status()
                data = resp.json()
                elements = data.get("elements", [])
                if elements:
                    print(f"Success: got {len(elements)} ATMs from {server}")
                    return elements
                else:
                    print("Got a response but 0 ATMs found in this bounding box.")
                    return elements
            except Exception as e:
                wait = 10 * (attempt + 1)
                print(f"Failed: {e}")
                print(f"Waiting {wait}s before retry...")
                time.sleep(wait)
    return []

def save_to_csv(elements, filename="real_atm_locations.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["atm_id", "name", "lat", "lon", "operator"])
        for el in elements:
            tags = el.get("tags", {})
            writer.writerow([
                el.get("id"),
                tags.get("name", "Unknown ATM"),
                el.get("lat"),
                el.get("lon"),
                tags.get("operator", tags.get("network", "Unknown")),
            ])
    print(f"Saved {len(elements)} ATMs to {filename}")

if __name__ == "__main__":
    atms = fetch_atms()
    if atms:
        save_to_csv(atms)
    else:
        print("No ATM data retrieved. Try a different city name or run again later.")
        sys.exit(1)