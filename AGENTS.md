# AGENTS.md

## Project

Predicts likely cash-withdrawal ATM locations for cybercrime fraud complaints in Bengaluru. Python scripts (no framework, no package manager manifest). Three-stage pipeline: fetch real ATM data → generate synthetic complaints → NLP entity extraction.

## Pipeline order (scripts must run sequentially)

1. `python Fetch_atms.py` — fetches ~1100 real ATM locations from OpenStreetMap Overpass API into `data/real_atm_locations.csv`. Makes live network calls with rate-limiting; may take several minutes.
2. `python generate_synthetic_data.py` — reads `data/real_atm_locations.csv`, writes 500 synthetic complaints to `data/synthetic_complaints.csv`. Requires step 1 output. Uses `seed(42)` for reproducibility.
3. `python nlp_extractor.py` — trains/loads a fraud-type classifier (TF-IDF + LogisticRegression) from `data/synthetic_complaints.csv`, saves model to `ml/fraud_type_classifier.joblib`. First run downloads the `en_core_web_sm` spaCy model.

## Dependencies (no requirements.txt — install manually)

```
pip install requests faker spacy scikit-learn joblib
python -m spacy download en_core_web_sm
```

## Key gotchas

- `Fetch_atms.py` hits public Overpass API servers; if all three servers in the fallback list fail, it exits with code 1. The CSV won't exist and downstream scripts will error.
- `generate_synthetic_data.py` hardcodes `data/real_atm_locations.csv` as input — path is not configurable via CLI args.
- `nlp_extractor.py` auto-trains on first run if `ml/fraud_type_classifier.joblib` is missing. The `ml/` directory must exist; create it if empty (`mkdir -p ml`).
- No test suite, no linter, no CI pipeline configured.
- `.gitignore` is a GitHub Python template; `venv/` and `ml/*.joblib` are excluded from version control.
