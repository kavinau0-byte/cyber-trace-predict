"""
Stands in for Person A's real NLP + GNN pipeline (Stages 2-3) until it's ready.

CONTRACT: predict() must return data matching PredictionResult exactly
(see /contracts/prediction_schema.json). When Person A's real model is ready,
swap the call in main.py from mock_ml.predict(...) to their real function --
nothing else in the backend should need to change if the shape matches.
"""
import random
from models import PredictionResult, PredictedZone


def predict(complaint_id: str, victim_lat: float, victim_lon: float) -> PredictionResult:
    """Fake but *plausible* prediction: a few zones scattered a short
    distance from the victim, with descending confidence -- mirroring the
    real model's expected ranked-zone output."""
    rng = random.Random(complaint_id)  # deterministic per complaint for demo stability

    zones = []
    for i in range(3):
        zones.append(
            PredictedZone(
                lat=victim_lat + rng.uniform(-0.05, 0.05),
                lon=victim_lon + rng.uniform(-0.05, 0.05),
                confidence=round(max(0.1, 0.9 - i * 0.25 + rng.uniform(-0.05, 0.05)), 2),
                radius_m=500,
            )
        )
    zones.sort(key=lambda z: z.confidence, reverse=True)

    mule_accounts = [f"MULE-{rng.randint(1000,9999)}" for _ in range(rng.randint(1, 3))]

    return PredictionResult(
        complaint_id=complaint_id,
        predicted_zones=zones,
        flagged_mule_accounts=mule_accounts,
    )
