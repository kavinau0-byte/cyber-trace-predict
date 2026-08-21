"""
Task 4 — Geospatial Location Predictor
Predicts likely ATM cash-withdrawal locations by combining:
  1. Graph GNN mule-chain confidence scores (from graph_model.py)
  2. DBSCAN geospatial clustering of historical withdrawal locations
  3. Victim-to-ATM distance plausibility models
"""

import csv
import json
import math
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN

# Support both package import and direct script execution
try:
    from ml.graph_model import build_graph, load_model, score_chain
except ImportError:
    from graph_model import build_graph, load_model, score_chain

COMPLAINTS_FILE = "data/synthetic_complaints.csv"
ATM_FILE = "data/real_atm_locations.csv"
EARTH_RADIUS_KM = 6371.0


# ---------------------------------------------------------------------------
# Utilities & Data Loading
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Compute Haversine distance in kilometers between two lat/lon coordinates."""
    R = EARTH_RADIUS_KM
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_complaints():
    """Load synthetic complaints CSV."""
    complaints = []
    with open(COMPLAINTS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["mule_chain"] = json.loads(row["mule_chain"])
            row["victim_lat"] = float(row["victim_lat"])
            row["victim_lon"] = float(row["victim_lon"])
            row["withdrawal_lat"] = float(row["withdrawal_lat"])
            row["withdrawal_lon"] = float(row["withdrawal_lon"])
            complaints.append(row)
    return complaints


def load_atms():
    """Load real ATM locations CSV."""
    atms = []
    with open(ATM_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                atms.append({
                    "atm_id": str(row["atm_id"]),
                    "name": str(row["name"]),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                })
            except (ValueError, KeyError):
                continue
    return atms


# ---------------------------------------------------------------------------
# Geospatial Hotspot Clustering (DBSCAN)
# ---------------------------------------------------------------------------

def compute_withdrawal_hotspots(complaints, eps_km=1.5, min_samples=3):
    """Run DBSCAN on historical withdrawal lat/lon coordinates.

    Args:
        complaints: list of complaint dicts containing withdrawal_lat / withdrawal_lon
        eps_km: clustering neighborhood radius in km (default 1.5km)
        min_samples: min points to form a cluster (default 3)

    Returns:
        list of cluster dicts:
            [{'centroid_lat': float, 'centroid_lon': float, 'density_score': float, 'sample_count': int}, ...]
    """
    coords_deg = np.array([[c["withdrawal_lat"], c["withdrawal_lon"]] for c in complaints])
    if len(coords_deg) == 0:
        return []

    # Convert coordinates to radians for Haversine DBSCAN
    coords_rad = np.radians(coords_deg)
    eps_rad = eps_km / EARTH_RADIUS_KM

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine")
    labels = db.fit_predict(coords_rad)

    unique_labels = set(labels) - {-1}
    hotspots = []
    total_pts = len(coords_deg)

    for lbl in unique_labels:
        cluster_pts = coords_deg[labels == lbl]
        count = len(cluster_pts)
        centroid_lat = float(np.mean(cluster_pts[:, 0]))
        centroid_lon = float(np.mean(cluster_pts[:, 1]))
        density_score = count / total_pts

        hotspots.append({
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            "density_score": density_score,
            "sample_count": count,
        })

    return hotspots


# ---------------------------------------------------------------------------
# Scoring Models
# ---------------------------------------------------------------------------

def victim_distance_score(d_km):
    """Score distance plausibility from victim (favors 2-15km range, peaking around 6km)."""
    if d_km < 0.5:
        return 0.05
    return math.exp(-((d_km - 6) ** 2) / (2 * 5 ** 2))


def hotspot_proximity_score(atm_lat, atm_lon, hotspots):
    """Compute proximity score to nearest historical hotspot centroid."""
    if not hotspots:
        return 0.5
    best_score = 0.0
    for hs in hotspots:
        d = haversine_km(atm_lat, atm_lon, hs["centroid_lat"], hs["centroid_lon"])
        prox = math.exp(-(d ** 2) / (2 * 2.0 ** 2)) * (1.0 + 2.0 * hs["density_score"])
        if prox > best_score:
            best_score = prox
    return min(best_score, 1.0)


# ---------------------------------------------------------------------------
# Location Prediction
# ---------------------------------------------------------------------------

def predict_withdrawal_zones(
    complaint_id: str,
    victim_lat: float,
    victim_lon: float,
    mule_chain: list[str],
    top_k: int = 3,
    atms: list = None,
    hotspots: list = None,
    base_graph=None,
    base_node_list=None,
) -> list[dict]:
    """Predict top_k likely ATM cash withdrawal locations for a complaint.

    Combines distance plausibility and hotspot proximity using chain_confidence as an interaction term:
        w_dist = 1.0 - (chain_confidence * 0.5)
        w_hotspot = 0.5 + (chain_confidence * 0.5)
        raw_score = (s_dist * w_dist) + (s_hotspot * w_hotspot)

    High confidence shifts weight toward historical hotspot patterns; low confidence shifts
    weight toward pure geospatial distance plausibility.

    Returns:
        list of top_k dicts: [{"atm_id": str, "name": str, "lat": float, "lon": float, "confidence": float}, ...]
    """
    if atms is None:
        atms = load_atms()
    if hotspots is None:
        complaints = load_complaints()
        hotspots = compute_withdrawal_hotspots(complaints)

    # (c) Mule chain GNN confidence score
    full_chain = [complaint_id] + list(mule_chain)
    try:
        mule_probs = score_chain(full_chain, base_graph=base_graph, base_node_list=base_node_list)
        mule_scores = mule_probs[1:] if len(mule_probs) > 1 else mule_probs
        chain_confidence = float(np.mean(mule_scores)) if mule_scores else 0.5
    except Exception:
        chain_confidence = 0.5

    # Compute interaction weights driven by chain_confidence
    w_dist = 1.0 - (chain_confidence * 0.5)
    w_hotspot = 0.5 + (chain_confidence * 0.5)

    # Filter candidate ATMs within 15km radius of victim
    candidates = []
    for atm in atms:
        d_victim = haversine_km(victim_lat, victim_lon, atm["lat"], atm["lon"])
        if d_victim > 15.0:
            continue

        s_dist = victim_distance_score(d_victim)
        s_hotspot = hotspot_proximity_score(atm["lat"], atm["lon"], hotspots)

        raw_score = (s_dist * w_dist) + (s_hotspot * w_hotspot)
        candidates.append((atm, raw_score))

    if not candidates:
        for atm in atms:
            d_victim = haversine_km(victim_lat, victim_lon, atm["lat"], atm["lon"])
            s_dist = victim_distance_score(d_victim)
            s_hotspot = hotspot_proximity_score(atm["lat"], atm["lon"], hotspots)
            raw_score = (s_dist * w_dist) + (s_hotspot * w_hotspot)
            candidates.append((atm, raw_score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    max_score = candidates[0][1] if candidates[0][1] > 0 else 1.0
    top_candidates = candidates[:top_k]

    results = []
    for atm, score in top_candidates:
        conf = min(round(float(score / max_score), 4), 1.0)
        results.append({
            "atm_id": atm["atm_id"],
            "name": atm["name"],
            "lat": atm["lat"],
            "lon": atm["lon"],
            "confidence": conf,
        })

    return results


# ---------------------------------------------------------------------------
# Sanity Check Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading data for location predictor sanity check...")
    complaints = load_complaints()
    atms = load_atms()
    print(f"  Loaded {len(complaints)} complaints and {len(atms)} ATMs.")

    print("Computing DBSCAN withdrawal hotspots...")
    hotspots = compute_withdrawal_hotspots(complaints)
    print(f"  Identified {len(hotspots)} hotspot clusters.")

    print("\nPre-building transaction graph for GNN inference...")
    base_graph, _ = build_graph(complaints)
    base_node_list = list(base_graph.nodes())

    sample_complaints = complaints[:3]
    print("\n" + "=" * 60)
    print("Running predict_withdrawal_zones() on 3 sample complaints:")
    print("=" * 60)

    for sc in sample_complaints:
        cid = sc["complaint_id"]
        vlat, vlon = sc["victim_lat"], sc["victim_lon"]
        mchain = sc["mule_chain"]
        actual_atm_id = str(sc["withdrawal_atm_id"])
        actual_atm_name = sc.get("withdrawal_atm_name", "N/A")

        predictions = predict_withdrawal_zones(
            complaint_id=cid,
            victim_lat=vlat,
            victim_lon=vlon,
            mule_chain=mchain,
            top_k=3,
            atms=atms,
            hotspots=hotspots,
            base_graph=base_graph,
            base_node_list=base_node_list,
        )

        print(f"\nComplaint: {cid}")
        print(f"  Victim Location : ({vlat:.4f}, {vlon:.4f})")
        print(f"  Mule Chain      : {' -> '.join(mchain)}")
        print(f"  Actual ATM      : [{actual_atm_id}] {actual_atm_name}")
        print(f"  Top Predicted ATM Withdrawal Zones:")
        for rank, pred in enumerate(predictions, 1):
            match_str = " (ACTUAL MATCH!)" if str(pred['atm_id']) == actual_atm_id else ""
            print(f"    Rank {rank}: [{pred['atm_id']}] {pred['name']:<35s} "
                  f"loc=({pred['lat']:.4f}, {pred['lon']:.4f})  conf={pred['confidence']:.4f}{match_str}")
