"""
Stage 6 — Real ML pipeline (Person A), replaces mock_ml as the prediction source.

Same call shape the backend already uses, now backed by:
  nlp_extractor.extract_entities()      -> bank + fraud type from complaint text
  location_predictor.predict_withdrawal_zones() -> ranked real-ATM predictions
  graph_model.score_chain()             -> per-account mule likelihood

All heavy artifacts (fraud classifier, GCN checkpoint, transaction graph,
DBSCAN hotspots) are loaded ONCE at module import, never per request.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
# Keep flat imports (models, etc.) working after the chdir below, regardless
# of how uvicorn was launched.
sys.path.insert(0, str(BACKEND_DIR))
# Person A's modules use repo-root-relative paths (data/, ml/) -- anchor CWD
# there regardless of where uvicorn was launched from.
os.chdir(REPO_ROOT)

import nlp_extractor
from ml import graph_model, location_predictor

from models import PredictedZone, PredictionResult

CLASSIFIER = nlp_extractor.load_or_train_classifier()

_COMPLAINTS = location_predictor.load_complaints()
_HOTSPOTS = location_predictor.compute_withdrawal_hotspots(_COMPLAINTS)
_ATMS = location_predictor.load_atms()
_GNN_MODEL, _GNN_NODE_LIST = graph_model.load_model()
_BASE_GRAPH, _ = graph_model.build_graph(_COMPLAINTS)

MULE_FLAG_THRESHOLD = 0.7


def predict(
    complaint_id: str,
    victim_lat: float,
    victim_lon: float,
    complaint_text: str,
    mule_chain: list[str],
) -> PredictionResult:
    entities = nlp_extractor.extract_entities(complaint_text, CLASSIFIER)

    zone_dicts = location_predictor.predict_withdrawal_zones(
        complaint_id=complaint_id,
        victim_lat=victim_lat,
        victim_lon=victim_lon,
        mule_chain=list(mule_chain),
        top_k=3,
        atms=_ATMS,
        hotspots=_HOTSPOTS,
        base_graph=_BASE_GRAPH,
        base_node_list=_GNN_NODE_LIST,
    )
    predicted_zones = sorted(
        (
            PredictedZone(
                lat=z["lat"],
                lon=z["lon"],
                confidence=z["confidence"],
                radius_m=500,  # fixed default; the real predictor emits no radius
                atm_id=z["atm_id"],
                name=z["name"],
            )
            for z in zone_dicts
        ),
        key=lambda z: z.confidence,
        reverse=True,
    )

    mule_scores = graph_model.score_chain(
        list(mule_chain),
        model=_GNN_MODEL,
        base_graph=_BASE_GRAPH,
        base_node_list=_GNN_NODE_LIST,
    )
    flagged_mule_accounts = [
        account
        for account, score in zip(mule_chain, mule_scores)
        if score > MULE_FLAG_THRESHOLD
    ]

    return PredictionResult(
        complaint_id=complaint_id,
        predicted_zones=predicted_zones,
        flagged_mule_accounts=flagged_mule_accounts,
    )
