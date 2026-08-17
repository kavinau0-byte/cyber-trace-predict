import requests
import time
import csv
import sys

# Greater Bengaluru — covers central + south (Electronics City, Hulimavu, HSR)
# + east (Whitefield) + surrounding areas where real reported cases happened
FULL_BBOX = {"south": 12.80, "west": 77.50, "north": 13.10, "east": 77.75}

# Split into a grid so each Overpass query stays small & fast (avoids timeouts)
GRID_ROWS = 3
GRID_COLS = 3

OVERPASS_SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

HEADERS = {
    "User-Agent": "SIH2026-CyberTracePredict/1.0 (student project, contact: kavinsihteam2026@gmail.com)"
}


def build_grid(bbox, rows, cols):
    lat_step = (bbox["north"] - bbox["south"]) / rows
    lon_step = (bbox["east"] - bbox["west"]) / cols
    cells = []
    for r in range(rows):
        for c in range(cols):
            s = bbox["south"] + r * lat_step
            n = s + lat_step
            w = bbox["west"] + c * lon_step
            e = w + lon_step
            cells.append(f"{s:.5f},{w:.5f},{n:.5f},{e:.5f}")
    return cells


def fetch_cell(bbox_str):
    query = f'[out:json][timeout:60];node["amenity"="atm"]({bbox_str});out body;'
    for server in OVERPASS_SERVERS:
        for attempt in range(2):
            try:
                resp = requests.post(server, data={"data": query}, headers=HEADERS, timeout=90)
                resp.raise_for_status()
                return resp.json().get("elements", [])
            except Exception as e:
                print(f"  cell {bbox_str} failed on {server} (attempt {attempt+1}): {e}")
                time.sleep(8)
    return []


def fetch_atms():
    cells = build_grid(FULL_BBOX, GRID_ROWS, GRID_COLS)
    all_elements = {}
    for i, cell in enumerate(cells, 1):
        print(f"Fetching grid cell {i}/{len(cells)}: {cell}")
        elements = fetch_cell(cell)
        for el in elements:
            all_elements[el["id"]] = el  # dedup by OSM node id
        print(f"  -> {len(elements)} ATMs (running total: {len(all_elements)})")
        time.sleep(2)  # be polite between cells
    return list(all_elements.values())

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