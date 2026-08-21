# Stage 6 Review — Mock → Real ML Pipeline Swap

Date: 2026-08-21 · Branch: `feature/backend-blockchain`

## What changed and why

Until now every `/complaints` request was scored by `mock_ml.predict()`, which
returned **random coordinates scattered near the victim** and a **random fake
mule account** — plausible-shaped noise, useful only for testing the API
plumbing. Stage 6 swaps that single call for Person A's real pipeline:

| Concern | Module | What it does |
|---|---|---|
| NLP | `nlp_extractor.extract_entities()` | Extracts bank name (spaCy PhraseMatcher) + fraud type (TF-IDF + LogReg classifier) from free complaint text |
| Geospatial + ranking | `ml.location_predictor.predict_withdrawal_zones()` | Ranks **real ATMs** from `data/real_atm_locations.csv` by distance plausibility × DBSCAN hotspot proximity, weighted by GNN chain confidence |
| GNN | `ml.graph_model.score_chain()` | Per-account mule-likelihood scores from a trained 2-layer GCN (`ml/mule_gnn.pt`) over the transaction graph |

### Files changed

- `backend/models.py` — added two optional fields to `PredictedZone`
  (`atm_id`, `name`). Nothing else touched.
- `backend/real_ml.py` — **new**. Drop-in replacement for `mock_ml`: same
  `predict(...)` entry point, extended signature
  `(complaint_id, victim_lat, victim_lon, complaint_text, mule_chain)`.
  All heavy artifacts (classifier joblib, GCN checkpoint, transaction graph,
  DBSCAN hotspots, ATM list) are loaded **once at module import**, never
  per-request.
- `backend/main.py` — exactly two lines of logic changed: `import mock_ml` →
  `import real_ml`, and the `predict(...)` call now passes
  `complaint.complaint_text` and `complaint.mule_chain`. **Blockchain
  logging, database calls, audit endpoints, and response structure are
  byte-for-byte untouched** (diff confirms: only the import line and the
  prediction call site).
- `backend/mock_ml.py` — kept for reference/fallback; no longer imported.
- `ml/location_predictor.py` — bugfix during integration: removed the
  `min(..., 1.0)` cap in `hotspot_proximity_score()` (see bugfix section).
- `requirements.txt` — added the NLP/ML runtime deps (`numpy`, `scikit-learn`,
  `joblib`, `spacy`, `en_core_web_sm` wheel).

### Files brought in from `feature/data-ml`

The ML code lives on Person A's branch, so these were checked out onto this
branch for integration:

```
nlp_extractor.py                      # NOTE: at repo ROOT, not inside ml/
ml/graph_model.py
ml/location_predictor.py
ml/fraud_type_classifier.joblib       # trained TF-IDF+LogReg fraud-type model
ml/mule_gnn.pt                        # trained GCN checkpoint
```

> Task description said `ml.nlp_extractor` — in reality Person A's module is
> at the repo root, so `real_ml.py` imports `nlp_extractor` (root) and
> `ml.location_predictor` / `ml.graph_model` (package). Same functions,
> actual location.

## Before / after — one sample complaint, side by side

Input: real row `CMP00001` from `data/synthetic_complaints.csv`
(victim at 12.995914, 77.553752 · Axis Bank · ₹7,300 · UPI QR Scam ·
mule chain `MULE-CP137038 → MULE-VC229305 → MULE-LN826220 → MULE-BL097800`).

### BEFORE — mock output (random nearby coordinates, fake mule)

```json
{
  "complaint_id": "CMP00001",
  "predicted_zones": [
    { "lat": 12.958953846909388, "lon": 77.57042820614173,  "confidence": 0.93, "radius_m": 500.0 },
    { "lat": 12.96586654092248,  "lon": 77.58975340397276,  "confidence": 0.68, "radius_m": 500.0 },
    { "lat": 13.009026233282123, "lon": 77.57918605395078,  "confidence": 0.42, "radius_m": 500.0 }
  ],
  "flagged_mule_accounts": [ "MULE-6993" ]
}
```

Zones are fabricated points with no ATM identity; the flagged account is a
random number that exists nowhere in the case data.

### AFTER — real output (actual POST /complaints response from the running server)

```json
{
  "complaint_id": "CMP00001",
  "prediction": {
    "complaint_id": "CMP00001",
    "predicted_zones": [
      {
        "lat": 12.9647139, "lon": 77.6056671, "confidence": 1.0,
        "radius_m": 500.0, "atm_id": "5168658572", "name": "Axis Bank"
      },
      {
        "lat": 12.9669962, "lon": 77.6140576, "confidence": 0.9868,
        "radius_m": 500.0, "atm_id": "9214580885", "name": "Unknown ATM"
      },
      {
        "lat": 12.965985, "lon": 77.6036918, "confidence": 0.9714,
        "radius_m": 500.0, "atm_id": "2774686318", "name": "Unknown ATM"
      }
    ],
    "flagged_mule_accounts": [ "MULE-CP137038", "MULE-VC229305" ]
  },
  "audit_tx_hashes": [
    "7ec74813bafb48cd90b4df5c4ace1fb5f31a2b7c9202a504624708ecec224738",
    "a2f44236ce26568c9292618ce511ed51da46c4d8c70e46bd13a3a241a1d8f665"
  ]
}
```

Verification performed against source data:

- All three `atm_id`s + coordinates match rows in `data/real_atm_locations.csv`
  exactly (e.g. `5168658572,Axis Bank,12.9647139,77.6056671`), i.e. real
  Bengaluru ATMs, not synthetic points.
- Confidences are genuinely rank-differentiated (1.0 → 0.9868 → 0.9714);
  see the confidence fix section below for why they started out identical.
- GNN mule-likelihood scores behind the flags (from `score_chain()`):

  | Account | Mule probability | Flagged (> 0.7)? |
  |---|---|---|
  | MULE-CP137038 | 0.9702 | yes |
  | MULE-VC229305 | 0.9059 | yes |
  | MULE-LN826220 | 0.6398 | no |
  | MULE-BL097800 | 0.1464 | no |

- Both audit events landed on-chain (`GET /audit/CMP00001` returns
  `complaint_received` + `prediction_generated` with payload hashes), and both
  rows persisted to SQLite — blockchain/DB flow unaffected by the swap.
- NLP extraction ran on the complaint text (extracted fraud type matches the
  row's label, bank matched via PhraseMatcher); its outputs are computed but
  not yet surfaced in `PredictionResult` (see limitations).

## Untouched-by-design

`blockchain_client.py`, `database.py`, the audit logging flow, endpoint
signatures, and `ComplaintResponse` are unmodified. The swap is confined to
the single prediction call, exactly as the Stage 4/5 contract intended.

## Bugfix — identical confidence 1.0 for all top-3 zones

**Symptom (first integration run).** Every predicted zone came back with
`confidence: 1.0`, e.g. ranks 1–3 all at exactly 1.0 for CMP00001:

```json
"predicted_zones": [
  { "atm_id": "10009343717", "confidence": 1.0, ... },
  { "atm_id": "9833588985",  "confidence": 1.0, ... },
  { "atm_id": "4843125823",  "confidence": 1.0, ... }
]
```

**Root cause.** Not the normalization itself — `predict_withdrawal_zones()`
already divides every candidate by the *shared* max raw score. Both score
components were saturating simultaneously:

- `hotspot_proximity_score()` applied `min(best_score, 1.0)`. The dominant
  DBSCAN hotspot holds 486/500 withdrawals (`density_score = 0.972`), so its
  density multiplier is ×2.94 and every ATM within ~2 km of the centroid
  capped at **exactly** 1.0.
- `victim_distance_score()` is a broad Gaussian (σ = 5 km), so all ATMs near
  the 6 km plausibility peak scored ≥ 0.9997.

Raw scores for the whole top tier therefore differed only in the 5th–6th
decimal (measured ratios to max: 1.0, 0.999997, 0.999995 …), and
`round(score / max_score, 4)` collapsed them all to 1.0.

**Fix.** Removed the `min(..., 1.0)` cap in `hotspot_proximity_score()`
(`ml/location_predictor.py`) so proximity stays continuous; the existing
shared-max normalization then produces genuine spread. Note this file comes
from Person A's `feature/data-ml` branch — the divergence needs to be merged
back there.

**After fix — same request, real output:**

| Rank | atm_id | name | confidence |
|---|---|---|---|
| 1 | 5168658572 | Axis Bank | 1.0 |
| 2 | 9214580885 | Unknown ATM | 0.9868 |
| 3 | 2774686318 | Unknown ATM | 0.9714 |

The values are tightly packed because the top candidates genuinely are close
in raw-score space (all near the hotspot centroid at plausible distances) —
they now reflect actual relative scores instead of a rounding artifact.
Ranking also shifted slightly vs. the pre-fix run: previously all saturated
ATMs were effectively tied and ordered by distance alone; ordering now also
reflects true hotspot proximity.

## Known limitations & assumptions

1. **Startup cost.** Module-level loading (classifier + GCN + graph build +
   DBSCAN hotspots) takes ≈ 5 s before the server accepts requests; measured
   4.97 s on this machine. First prediction adds ≈ 3.8 s (betweenness
   centrality recomputation inside `score_chain`); subsequent predictions are
   faster.
2. **Double GNN inference per request.** `predict_withdrawal_zones()` calls
   `score_chain()` internally (for chain-confidence weighting) and
   `real_ml.predict()` calls it again for per-account flags. Correct but
   redundant work; fine at demo scale, worth merging later.
3. **Classifier retrains if artifact missing.** `load_or_train_classifier()`
   falls back to a full retrain from `data/synthetic_complaints.csv` if
   `ml/fraud_type_classifier.joblib` is absent — silent multi-second startup
   and a different model than the committed artifact. The joblib is checked
   in, so this only bites if someone deletes it.
4. **`radius_m` is a fixed 500.** The real predictor emits no radius; the
   field is kept for contract compatibility with dashboard circle rendering.
5. **Confidence is relative, not absolute.** Scores are normalized against the
   best candidate for that complaint (`score / max_score`), so the top zone is
   always 1.0 and confidences aren't comparable across complaints — only
   within one complaint's ranking. Because the top candidates in a dense city
   grid are often genuinely close, ranks 2–3 can sit just under rank 1
   (e.g. 0.987 / 0.971); that's real score proximity, not a bug.
6. **NLP outputs are computed but unused.** `extracted_bank` /
   `extracted_fraud_type` don't fit the current `PredictionResult` contract;
   they're extracted per the Stage 6 plan but not yet stored or returned.
   Wiring them into the DB/response requires a contract change (both
   `prediction_schema.json` and `models.py` together).
7. **CWD anchoring.** Person A's modules resolve `data/…` and `ml/…` relative
   to the working directory, while the backend historically runs from
   `backend-blockchain/backend/`. `real_ml.py` therefore `chdir`s to the repo
   root at import and pins both the repo root and backend dir on `sys.path`,
   so the documented launch command still works from either directory.
   Observed side effect: none — SQLite resolves its relative path at engine
   creation (before the chdir), so `cybertrace.db` still lands in
   `backend-blockchain/backend/`.
8. **Runtime dependencies.** The backend needs the API deps *plus* the ML
   stack: `spacy` (+ `en_core_web_sm`), `scikit-learn`, `joblib`, `numpy`,
   `torch`, `torch-geometric`, `networkx`, `pandas`. The NLP-side deps are now
   pinned in `backend-blockchain/requirements.txt` (including the
   `en_core_web_sm` wheel URL, since spaCy models aren't on PyPI); the torch
   training stack is still only in the shared root venv.
9. **Top-3 recall is not guaranteed.** For CMP00001 the actual withdrawal ATM
   (`5915230906`, 10.21 km from victim) did not appear in the top-3. Expected
   for a ranked-prediction system; hit-rate evaluation belongs to Person A's
   offline benchmarks, not this integration.
10. **OSM data quality.** Several real ATMs have `name = "Unknown ATM"`
    (missing OSM tags) — cosmetic, ids remain authoritative.

## How to reproduce

```bash
cd backend-blockchain/backend
../../venv/bin/uvicorn main:app --port 8000     # ~5 s model loading at startup
# POST CMP00001 as above -> real ATM zones + GNN-flagged mules
curl http://127.0.0.1:8000/audit/CMP00001       # both events on-chain
```
