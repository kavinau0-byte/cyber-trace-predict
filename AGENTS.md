# AGENTS.md

SIH2026 student project: predict cash-withdrawal locations for cybercrime complaints (GNN mule-account tracing + geospatial clustering + NLP), with a blockchain audit trail and FastAPI backend. Team split: "Person A" = data/ML, "Person B" = backend/blockchain (Stages 4–5 done).

## Layout trap

- Root-level `backend/` and `dashboard/` are **empty placeholders** (only `__pycache__` / untracked build artifacts). Do not assume they contain code.
- All committed code lives in `backend-blockchain/` plus root scripts `generate_synthetic_data.py`, `Fetch_atms.py`, and `nlp_extractor.py`; datasets in `data/`. The ML pipeline (`ml/graph_model.py`, `ml/location_predictor.py`, model artifacts) was checked out from `feature/data-ml` for the Stage 6 integration — keep it in sync with that branch.
- `dashboard/dist/` holds built assets but there is no frontend source in git yet.
- The root `venv/` (Python 3.14) is shared by everything. Its ML deps (torch, torch-geometric, networkx, pandas, faker, spacy + en_core_web_sm, scikit-learn, joblib) are **not pinned anywhere** — the only requirements file is `backend-blockchain/requirements.txt`, which covers only the API deps (and itself wasn't fully installed in the venv until Stage 6; run `pip install -r backend-blockchain/requirements.txt` if web3/sqlmodel imports fail).

## Commands

- Run the API (must run from that dir — imports are flat, e.g. `from models import ...`):
  ```bash
  cd backend-blockchain/backend && ../../venv/bin/uvicorn main:app --reload --port 8000
  ```
  Swagger UI at http://127.0.0.1:8000/docs. Verify manually with curl or Swagger — there are no tests, lint config, or CI in this repo.
- Regenerate data (run from repo root; paths are CWD-relative):
  ```bash
  python generate_synthetic_data.py   # reads data/real_atm_locations.csv -> writes data/synthetic_complaints.csv
  ```
  Seeded (`random.seed(42)`) for reproducibility; remove the seed for fresh data.
- `Fetch_atms.py` writes `real_atm_locations.csv` to the **CWD**, not `data/` — move it after fetching or `generate_synthetic_data.py` won't find it.
- Recompile Solidity after editing `AuditTrail.sol` (compiled artifact `AuditTrail.json` is checked in):
  ```bash
  cd backend-blockchain/blockchain && npm install solc@0.8.20 && node compile.js
  ```

## Blockchain gotchas

- `blockchain_client.py` uses **eth-tester**, an in-memory chain: no Ganache/Hardhat needed, but the contract redeploys and the audit trail resets on every server restart. Only sha256 payload hashes go on-chain, never raw payloads.
- To use a persistent local testnet, swap `EthereumTesterProvider()` for `Web3.HTTPProvider("http://127.0.0.1:8545")` — nothing else changes.

## Contracts are the interface

- `backend-blockchain/contracts/{complaint,prediction}_schema.json` define the Person A ↔ Person B boundary. Pydantic models in `backend/models.py` mirror them — update both together, never let them drift.
- The real-ML swap is done (Stage 6): `main.py` calls `real_ml.predict(...)`, which wraps the ml/ pipeline. `mock_ml.py` is kept as a fallback. See `backend/STAGE6_REVIEW.md` for the swap details and known limitations.

## Database

SQLite (`cybertrace.db`, gitignored) is created at the CWD where uvicorn runs. Postgres+PostGIS swap per project plan touches only `DATABASE_URL` in `backend/database.py`.

## Git workflow

Feature branches (`feature/backend-blockchain`, `feature/data-ml`, `feature/frontend`) merge into `dev` every 2–3 days per the project plan — don't leave work unmerged until integration stages.
