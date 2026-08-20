# CyberTrace Predict — Backend + Blockchain Layer (Person B)

Covers Stage 4 (blockchain audit) and Stage 5 (backend API) from the project plan.
Everything below has been run and verified end-to-end — including against a real
row from `generate_synthetic_data.py`'s actual output, not just hand-typed test data.

## What's in here

```
contracts/
  complaint_schema.json     <- input contract: matches generate_synthetic_data.py fields
  prediction_schema.json    <- output contract: what Person A's model must return

blockchain/
  AuditTrail.sol             <- the Stage 4 smart contract
  compile.js                 <- compiles it to ABI + bytecode (AuditTrail.json)

backend/
  models.py                  <- Pydantic models mirroring the two JSON contracts
  mock_ml.py                 <- stands in for Person A's model until Stage 6
  blockchain_client.py       <- web3.py wrapper: deploy + logEvent + getAuditTrail
  database.py                <- SQLite now, swap to Postgres+PostGIS later
  main.py                    <- FastAPI app tying it all together

requirements.txt
```

## Setup (one time)

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The smart contract is already compiled (`blockchain/AuditTrail.json` is checked in).
If you edit `AuditTrail.sol`, recompile with Node:

```bash
cd blockchain
npm install solc@0.8.20
node compile.js
```

## Run the API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger docs — you can fire
requests straight from the browser.

Note: `blockchain_client.py` uses `eth-tester`, an in-memory Ethereum chain — no
Ganache/Hardhat node needed to run this. It resets every time you restart the
server (fine for dev; that's what a "local testnet" means at this stage). When
you want a persistent chain for the demo, swap `EthereumTesterProvider()` for
`Web3.HTTPProvider("http://127.0.0.1:8545")` pointed at a running Hardhat/Ganache
node — the contract code and API don't change, only the connection.

## Try it

```bash
curl -X POST http://127.0.0.1:8000/complaints -H "Content-Type: application/json" -d '{
  "complaint_id": "CMP00001",
  "victim_lat": 12.9716,
  "victim_lon": 77.5946,
  "fraud_type": "otp_fraud",
  "bank": "HDFC",
  "amount_inr": 40000,
  "complaint_text": "Someone called pretending to be from my bank and asked for OTP"
}'

curl http://127.0.0.1:8000/predictions/CMP00001
curl http://127.0.0.1:8000/audit/CMP00001
```

You can also pipe real rows straight out of
`data/synthetic_complaints.csv` — the field names match `ComplaintIn` exactly,
since that's Person A's actual data dictionary.

## The Stage 6 swap (mock → real ML)

Everything routes through one call in `backend/main.py`:

```python
prediction: PredictionResult = mock_ml.predict(
    complaint.complaint_id, complaint.victim_lat, complaint.victim_lon
)
```

When Person A's NLP+GNN pipeline is ready, this becomes:

```python
from real_ml import predict  # Person A's module
prediction: PredictionResult = predict(complaint)
```

**This only works if Person A's function returns data matching
`PredictionResult` in `models.py` / `prediction_schema.json` exactly** — same
field names, same types, `predicted_zones` sorted by confidence descending.
Get their sign-off on that contract before either of you writes more code.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/complaints` | Intake → mock/real ML → blockchain log → DB save |
| GET | `/complaints/{id}` | Fetch stored complaint |
| GET | `/predictions/{id}` | Fetch stored prediction |
| GET | `/audit/{id}` | Full on-chain audit trail for a complaint |
| GET | `/health` | Liveness + deployed contract address |

## Swapping SQLite for Postgres + PostGIS (per the project plan)

Only `backend/database.py` needs to change:

```python
DATABASE_URL = "postgresql://user:pass@localhost:5432/cybertrace"
```

Add `geoalchemy2` and a `Geometry` column for `victim_lat/lon` and predicted
zone centers once the dashboard (Stage 7) needs proximity queries
("find complaints near this ATM"). Table/column names elsewhere stay the same.

## Git workflow reminder

Do this work on `feature/backend-blockchain`, merge into `dev` every 2–3 days
per the project plan — don't let it sit unmerged until Stage 6, or the ML swap
turns into a painful integration day instead of a one-line change.
