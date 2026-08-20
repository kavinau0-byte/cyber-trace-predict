"""
FastAPI orchestrator (Stage 5). Run with:
    uvicorn main:app --reload --port 8000

Then open http://127.0.0.1:8000/docs for interactive API docs.

Flow per complaint:
  POST /complaints
    -> validate against ComplaintIn contract
    -> save to DB
    -> log "complaint_received" to blockchain
    -> call mock_ml.predict() (swap for Person A's real model at Stage 6)
    -> save prediction to DB
    -> log "prediction_generated" to blockchain
    -> return PredictionResult + audit tx hashes
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from sqlmodel import Session

from models import ComplaintIn, PredictionResult, AuditEntryOut, ComplaintResponse
from database import engine, init_db, save_complaint, save_prediction, Complaint, Prediction
from blockchain_client import audit_chain
import mock_ml
import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="CyberTrace Predict — Backend API", lifespan=lifespan)


@app.post("/complaints", response_model=ComplaintResponse)
def receive_complaint(complaint: ComplaintIn):
    tx_hashes = []

    with Session(engine) as session:
        save_complaint(session, complaint)

    tx1 = audit_chain.log_event(
        complaint.complaint_id, "complaint_received", complaint.model_dump()
    )
    tx_hashes.append(tx1)

    # --- Person A's real model plugs in here at Stage 6 ---
    prediction: PredictionResult = mock_ml.predict(
        complaint.complaint_id, complaint.victim_lat, complaint.victim_lon
    )

    with Session(engine) as session:
        save_prediction(session, prediction)

    tx2 = audit_chain.log_event(
        complaint.complaint_id, "prediction_generated", prediction.model_dump()
    )
    tx_hashes.append(tx2)

    return ComplaintResponse(
        complaint_id=complaint.complaint_id,
        prediction=prediction,
        audit_tx_hashes=tx_hashes,
    )


@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: str):
    with Session(engine) as session:
        row = session.get(Complaint, complaint_id)
        if not row:
            raise HTTPException(404, "complaint not found")
        return json.loads(row.raw_json)


@app.get("/predictions/{complaint_id}", response_model=PredictionResult)
def get_prediction(complaint_id: str):
    with Session(engine) as session:
        row = session.get(Prediction, complaint_id)
        if not row:
            raise HTTPException(404, "prediction not found")
        return PredictionResult(
            complaint_id=row.complaint_id,
            predicted_zones=json.loads(row.predicted_zones_json),
            flagged_mule_accounts=json.loads(row.flagged_mule_accounts_json),
        )


@app.get("/audit/{complaint_id}", response_model=list[AuditEntryOut])
def get_audit_trail(complaint_id: str):
    trail = audit_chain.get_audit_trail(complaint_id)
    if not trail:
        raise HTTPException(404, "no audit entries for this complaint")
    return trail


@app.get("/health")
def health():
    return {"status": "ok", "contract_address": audit_chain.address}
