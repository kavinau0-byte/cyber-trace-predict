"""
Pydantic models mirroring /contracts/*.json exactly.
If Person A changes the prediction contract shape, update PredictionResult here
and in the JSON file together — never let them drift apart.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ---- Input contract: matches generate_synthetic_data.py fields ----
class ComplaintIn(BaseModel):
    complaint_id: str
    victim_lat: float
    victim_lon: float
    fraud_type: str
    bank: str
    amount_inr: float
    complaint_text: str
    incident_time: Optional[str] = None
    complaint_time: Optional[str] = None
    mule_chain: Optional[list[str]] = Field(default_factory=list)
    withdrawal_atm_id: Optional[str] = None
    withdrawal_atm_name: Optional[str] = None
    withdrawal_lat: Optional[float] = None
    withdrawal_lon: Optional[float] = None
    withdrawal_time: Optional[str] = None
    victim_to_withdrawal_km: Optional[float] = None


# ---- Output contract: matches Person A's NLP+GNN prediction shape ----
class PredictedZone(BaseModel):
    lat: float
    lon: float
    confidence: float
    radius_m: float
    atm_id: Optional[str] = None
    name: Optional[str] = None


class PredictionResult(BaseModel):
    complaint_id: str
    predicted_zones: list[PredictedZone]
    flagged_mule_accounts: list[str] = Field(default_factory=list)


# ---- API response wrappers ----
class AuditEntryOut(BaseModel):
    complaint_id: str
    event_type: str
    payload_hash: str
    timestamp: int
    logged_by: str


class ComplaintResponse(BaseModel):
    complaint_id: str
    prediction: PredictionResult
    audit_tx_hashes: list[str]
