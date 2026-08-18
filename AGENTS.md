# AGENTS.md

## Project

Predicts likely cash-withdrawal ATM locations for cybercrime fraud complaints in Bengaluru. Two independent parts:
- **Python pipeline** — fetch real ATM data → generate synthetic complaints → NLP entity extraction (no framework, no package manifest)
- **React dashboard** (`dashboard/`) — Vite + TypeScript + Tailwind v4 + Leaflet map, currently uses hardcoded mock data (`src/data/mockData.ts`), not wired to pipeline CSVs

## Python pipeline order

1. `python Fetch_atms.py` — fetches ~1100 real ATM locations from OpenStreetMap Overpass API into `data/real_atm_locations.csv`. Live network calls with rate-limiting; may take several minutes.
2. `python generate_synthetic_data.py` — reads `data/real_atm_locations.csv`, writes 500 synthetic complaints to `data/synthetic_complaints.csv`. Requires step 1 output. Uses `seed(42)`.
3. `python nlp_extractor.py` — trains/loads a fraud-type classifier (TF-IDF + LogisticRegression), saves model to `ml/fraud_type_classifier.joblib`. First run downloads `en_core_web_sm` spaCy model.

## Python dependencies (no requirements.txt)

```
pip install requests faker spacy scikit-learn joblib
python -m spacy download en_core_web_sm
```

## Dashboard commands (run inside `dashboard/`)

```
npm install          # install deps (node_modules already present)
npm run dev          # Vite dev server
npm run build        # tsc -b && vite build
npm run lint         # oxlint (NOT eslint)
npm run preview      # serve production build
```

## Key gotchas

- `Fetch_atms.py` hits public Overpass API servers; if all three in the fallback list fail, it exits code 1. Downstream scripts will error on missing CSV.
- `generate_synthetic_data.py` hardcodes `data/real_atm_locations.csv` — path not configurable via CLI.
- `nlp_extractor.py` auto-trains on first run if `ml/fraud_type_classifier.joblib` is missing. `ml/` dir must exist (`mkdir -p ml`).
- Dashboard uses `oxlint` (not eslint) — config in `dashboard/.oxlintrc.json`.
- Dashboard path alias: `@/` maps to `src/` (Vite + tsconfig).
- Dashboard data is entirely mock — `src/data/mockData.ts` generates random complaints/predictions/audit entries on import. No backend or CSV loading.
- No test suite, no CI pipeline, no Python linter configured.
- `.gitignore` is a GitHub Python template; `venv/` and `ml/*.joblib` excluded from VCS.
