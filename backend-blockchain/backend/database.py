"""
SQLite for local dev/demo (zero setup). For the real deployment per the
project plan, swap DATABASE_URL to Postgres + PostGIS, e.g.:

    postgresql://user:pass@localhost:5432/cybertrace

and add geoalchemy2 for the geo columns (victim location, predicted zones)
so the dashboard can do proximity queries. The table shapes below stay the
same either way -- only the engine URL changes.
"""
import json
from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = "sqlite:///./cybertrace.db"
engine = create_engine(DATABASE_URL, echo=False)


class Complaint(SQLModel, table=True):
    complaint_id: str = Field(primary_key=True)
    victim_lat: float
    victim_lon: float
    fraud_type: str
    bank: str
    amount_inr: float
    complaint_text: str
    raw_json: str  # full original payload, for audit/debug


class Prediction(SQLModel, table=True):
    complaint_id: str = Field(primary_key=True)
    predicted_zones_json: str
    flagged_mule_accounts_json: str


def init_db():
    SQLModel.metadata.create_all(engine)


def save_complaint(session: Session, complaint) -> None:
    row = Complaint(
        complaint_id=complaint.complaint_id,
        victim_lat=complaint.victim_lat,
        victim_lon=complaint.victim_lon,
        fraud_type=complaint.fraud_type,
        bank=complaint.bank,
        amount_inr=complaint.amount_inr,
        complaint_text=complaint.complaint_text,
        raw_json=complaint.model_dump_json(),
    )
    session.merge(row)
    session.commit()


def save_prediction(session: Session, prediction) -> None:
    row = Prediction(
        complaint_id=prediction.complaint_id,
        predicted_zones_json=json.dumps([z.model_dump() for z in prediction.predicted_zones]),
        flagged_mule_accounts_json=json.dumps(prediction.flagged_mule_accounts),
    )
    session.merge(row)
    session.commit()
