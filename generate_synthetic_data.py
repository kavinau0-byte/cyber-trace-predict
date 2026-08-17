"""
Task 2 — Synthetic Complaint Dataset Generator
Generates realistic fake fraud complaints, but withdrawal locations are
picked from REAL Bengaluru ATM data (real_atm_locations.csv) — only the
complaint/victim/mule-chain details are simulated.
"""

import csv
import json
import random
import math
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_IN")
random.seed(42)  # reproducible dataset — remove this line if you want fresh data each run

# ---------- Config ----------
NUM_COMPLAINTS = 500
ATM_FILE = "data/real_atm_locations.csv"
OUTPUT_FILE = "data/synthetic_complaints.csv"

# Central Bengaluru bbox (same area as the ATM fetch)
LAT_RANGE = (12.90, 13.05)
LON_RANGE = (77.55, 77.70)

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Bank of Baroda",
         "Punjab National Bank", "Kotak Mahindra Bank", "Canara Bank"]

FRAUD_TYPES = {
    "OTP Phishing": "I received a call from someone claiming to be a {bank} representative. "
                     "They asked me to share the OTP for a 'card upgrade' and my account was "
                     "debited immediately after.",
    "Fake Loan App": "I applied for a quick personal loan through an app I found online. "
                      "After paying a 'processing fee' the app disappeared and my money is gone.",
    "UPI QR Scam": "Someone posing as a buyer on an online marketplace asked me to scan a QR code "
                    "to 'receive' payment. Instead, money was deducted from my {bank} account.",
    "Job Fraud": "I was offered a work-from-home job and asked to pay a 'registration fee' "
                 "via UPI. The recruiter stopped responding after I paid.",
    "KYC Update Scam": "I got a message saying my {bank} KYC would expire unless I updated it "
                        "via a link. After entering my details, money was withdrawn from my account.",
    "Investment Fraud": "I invested in a trading scheme promoted on social media that promised "
                         "high returns. The platform is no longer accessible and I've lost my money.",
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def load_atms():
    atms = []
    with open(ATM_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                atms.append({
                    "atm_id": row["atm_id"],
                    "name": row["name"],
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                })
            except (ValueError, KeyError):
                continue
    return atms


def pick_withdrawal_atm(victim_lat, victim_lon, atms):
    """Weighted pick favoring ATMs roughly 2-15km away (realistic mule cash-out range),
    peaking around 5-8km — not too close (traceable), not too far (impractical)."""
    weighted = []
    for atm in atms:
        d = haversine_km(victim_lat, victim_lon, atm["lat"], atm["lon"])
        if d < 0.5:
            weight = 0.05
        else:
            # peak around 6km, decays smoothly on both sides
            weight = math.exp(-((d - 6) ** 2) / (2 * 5 ** 2))
        weighted.append((atm, weight, d))

    total = sum(w for _, w, _ in weighted)
    r = random.uniform(0, total)
    upto = 0
    for atm, w, d in weighted:
        upto += w
        if upto >= r:
            return atm, d
    return weighted[-1][0], weighted[-1][2]


def generate_mule_chain():
    hops = random.randint(2, 4)
    return [f"MULE-{fake.bothify('??######').upper()}" for _ in range(hops)]


def random_amount():
    # log-normal-ish distribution: mostly mid-range, occasional big losses
    return round(random.lognormvariate(10, 0.9), -2)  # rounds to nearest 100


def generate_complaint(complaint_id, atms):
    victim_lat = random.uniform(*LAT_RANGE)
    victim_lon = random.uniform(*LON_RANGE)

    fraud_type = random.choice(list(FRAUD_TYPES.keys()))
    bank = random.choice(BANKS)
    complaint_text = FRAUD_TYPES[fraud_type].format(bank=bank)

    incident_time = fake.date_time_between(start_date="-30d", end_date="now")
    # victims usually report within a few hours to ~2 days
    report_delay_hours = random.uniform(0.5, 48)
    complaint_time = incident_time + timedelta(hours=report_delay_hours)

    # mule withdrawal happens 6-48 hours after the incident
    withdrawal_delay_hours = random.uniform(6, 48)
    withdrawal_time = incident_time + timedelta(hours=withdrawal_delay_hours)

    atm, distance_km = pick_withdrawal_atm(victim_lat, victim_lon, atms)
    mule_chain = generate_mule_chain()
    amount = min(random_amount(), 500000)
    amount = max(amount, 2000)

    return {
        "complaint_id": f"CMP{complaint_id:05d}",
        "victim_lat": round(victim_lat, 6),
        "victim_lon": round(victim_lon, 6),
        "fraud_type": fraud_type,
        "bank": bank,
        "amount_inr": amount,
        "complaint_text": complaint_text,
        "incident_time": incident_time.isoformat(),
        "complaint_time": complaint_time.isoformat(),
        "mule_chain": json.dumps(mule_chain),
        "withdrawal_atm_id": atm["atm_id"],
        "withdrawal_atm_name": atm["name"],
        "withdrawal_lat": atm["lat"],
        "withdrawal_lon": atm["lon"],
        "withdrawal_time": withdrawal_time.isoformat(),
        "victim_to_withdrawal_km": round(distance_km, 2),
    }


def main():
    atms = load_atms()
    if not atms:
        print(f"No ATM data found in {ATM_FILE}. Run fetch_atms.py first.")
        return

    print(f"Loaded {len(atms)} real ATM locations.")
    complaints = [generate_complaint(i + 1, atms) for i in range(NUM_COMPLAINTS)]

    fieldnames = list(complaints[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(complaints)

    print(f"Generated {len(complaints)} synthetic complaints -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()