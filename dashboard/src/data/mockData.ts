// Mock data matching the synthetic data schema from generate_synthetic_data.py

export interface Complaint {
  complaint_id: string;
  victim_lat: number;
  victim_lon: number;
  fraud_type: string;
  bank: string;
  amount_inr: number;
  complaint_text: string;
  incident_time: string;
  complaint_time: string;
  mule_chain: string[];
  withdrawal_atm_id: string;
  withdrawal_atm_name: string;
  withdrawal_lat: number;
  withdrawal_lon: number;
  withdrawal_time: string;
  victim_to_withdrawal_km: number;
}

export interface Prediction {
  id: string;
  zone_name: string;
  center_lat: number;
  center_lon: number;
  radius_km: number;
  confidence: number;
  complaint_count: number;
  fraud_types: string[];
  risk_level: "critical" | "high" | "medium";
  trend: "rising" | "stable" | "declining";
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details: string;
  actor: string;
  block_hash: string;
}

const FRAUD_TYPES = [
  "OTP Phishing",
  "Fake Loan App",
  "UPI QR Scam",
  "Job Fraud",
  "KYC Update Scam",
  "Investment Fraud",
];

const BANKS = [
  "SBI",
  "HDFC Bank",
  "ICICI Bank",
  "Axis Bank",
  "Bank of Baroda",
  "Punjab National Bank",
  "Kotak Mahindra Bank",
  "Canara Bank",
];

const ATM_NAMES = [
  "SBI Koramangala ATM",
  "HDFC Indiranagar Branch",
  "ICICI ATM MG Road",
  "Axis Bank Jayanagar",
  "SBI Whitefield ATM",
  "HDFC Electronic City",
  "Canara Bank HSR Layout",
  "PNB ATM BTM Layout",
  "Kotak ATM Bannerghatta Rd",
  "SBI JP Nagar ATM",
];

const ZONE_NAMES = [
  "Koramangala–HSR Cluster",
  "Whitefield Corridor",
  "Electronic City Hub",
  "MG Road–Brigade Zone",
  "Jayanagar–JP Nagar Belt",
  "BTM–Hebbal Ring",
];

const ACTORS = [
  "system-auto",
  "analyst-01",
  "analyst-02",
  "investigator-01",
];

const ACTIONS = [
  "complaint.ingested",
  "prediction.generated",
  "hotspot.flagged",
  "mule_account.linked",
  "alert.dispatched",
  "case.escalated",
  "atm.zone.marked",
];

function randomBetween(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function randomItem<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateHash(): string {
  return "0x" + Array.from({ length: 16 }, () =>
    Math.floor(Math.random() * 16).toString(16)
  ).join("");
}

// Seed a deterministic-ish set of complaints for demo
export const complaints: Complaint[] = Array.from({ length: 50 }, (_, i) => {
  const victimLat = randomBetween(12.85, 13.05);
  const victimLon = randomBetween(77.52, 77.72);
  const withdrawLat = victimLat + randomBetween(-0.06, 0.06);
  const withdrawLon = victimLon + randomBetween(-0.06, 0.06);
  const fraudType = FRAUD_TYPES[i % FRAUD_TYPES.length];
  const bank = BANKS[i % BANKS.length];
  const incident = new Date(Date.now() - randomBetween(1, 72) * 3600000);

  return {
    complaint_id: `CMP${String(i + 1).padStart(5, "0")}`,
    victim_lat: +victimLat.toFixed(6),
    victim_lon: +victimLon.toFixed(6),
    fraud_type: fraudType,
    bank,
    amount_inr: Math.round(randomBetween(2000, 450000) / 100) * 100,
    complaint_text: `Victim reported ${fraudType.toLowerCase()} involving ${bank}.`,
    incident_time: incident.toISOString(),
    complaint_time: new Date(
      incident.getTime() + randomBetween(0.5, 48) * 3600000
    ).toISOString(),
    mule_chain: Array.from(
      { length: Math.floor(randomBetween(2, 5)) },
      (_, j) => `MULE-${String.fromCharCode(65 + j)}${Math.floor(Math.random() * 999999)}`
    ),
    withdrawal_atm_id: `ATM${1000 + i}`,
    withdrawal_atm_name: ATM_NAMES[i % ATM_NAMES.length],
    withdrawal_lat: +withdrawLat.toFixed(6),
    withdrawal_lon: +withdrawLon.toFixed(6),
    withdrawal_time: new Date(
      incident.getTime() + randomBetween(6, 48) * 3600000
    ).toISOString(),
    victim_to_withdrawal_km: +randomBetween(1.5, 18).toFixed(2),
  };
});

export const predictions: Prediction[] = [
  {
    id: "PRED-001",
    zone_name: ZONE_NAMES[0],
    center_lat: 12.9116,
    center_lon: 77.6389,
    radius_km: 2.4,
    confidence: 0.94,
    complaint_count: 12,
    fraud_types: ["OTP Phishing", "KYC Update Scam"],
    risk_level: "critical",
    trend: "rising",
  },
  {
    id: "PRED-002",
    zone_name: ZONE_NAMES[1],
    center_lat: 12.9698,
    center_lon: 77.75,
    radius_km: 3.1,
    confidence: 0.87,
    complaint_count: 9,
    fraud_types: ["Investment Fraud", "Fake Loan App"],
    risk_level: "high",
    trend: "rising",
  },
  {
    id: "PRED-003",
    zone_name: ZONE_NAMES[2],
    center_lat: 12.8454,
    center_lon: 77.6589,
    radius_km: 2.8,
    confidence: 0.81,
    complaint_count: 7,
    fraud_types: ["UPI QR Scam"],
    risk_level: "high",
    trend: "stable",
  },
  {
    id: "PRED-004",
    zone_name: ZONE_NAMES[3],
    center_lat: 12.9755,
    center_lon: 77.6083,
    radius_km: 1.6,
    confidence: 0.72,
    complaint_count: 5,
    fraud_types: ["Job Fraud", "OTP Phishing"],
    risk_level: "medium",
    trend: "declining",
  },
  {
    id: "PRED-005",
    zone_name: ZONE_NAMES[4],
    center_lat: 12.8888,
    center_lon: 77.5955,
    radius_km: 2.9,
    confidence: 0.89,
    complaint_count: 11,
    fraud_types: ["OTP Phishing", "Fake Loan App", "UPI QR Scam"],
    risk_level: "critical",
    trend: "rising",
  },
  {
    id: "PRED-006",
    zone_name: ZONE_NAMES[5],
    center_lat: 12.985,
    center_lon: 77.555,
    radius_km: 2.2,
    confidence: 0.68,
    complaint_count: 4,
    fraud_types: ["KYC Update Scam"],
    risk_level: "medium",
    trend: "stable",
  },
];

export const auditLog: AuditEntry[] = Array.from({ length: 20 }, (_, i) => {
  const action = ACTIONS[i % ACTIONS.length];
  const timestamp = new Date(Date.now() - i * randomBetween(300000, 1800000));
  const entityType = action.split(".")[0];
  const entityId =
    entityType === "complaint"
      ? `CMP${String(Math.floor(randomBetween(1, 50))).padStart(5, "0")}`
      : entityType === "mule_account"
        ? `MULE-${String.fromCharCode(65 + Math.floor(Math.random() * 5))}${Math.floor(Math.random() * 999999)}`
        : entityType === "hotspot" || entityType === "prediction"
          ? `PRED-${String(Math.floor(randomBetween(1, 6))).padStart(3, "0")}`
          : `ATM${Math.floor(randomBetween(1000, 1050))}`;

  return {
    id: `TX${String(i + 1).padStart(6, "0")}`,
    timestamp: timestamp.toISOString(),
    action,
    entity_type: entityType,
    entity_id: entityId,
    details: `${action.replace(".", " ").replace("_", " ")} recorded for ${entityId}`,
    actor: randomItem(ACTORS),
    block_hash: generateHash(),
  };
}).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

// Summary stats
export const stats = {
  totalComplaints: complaints.length,
  totalAmountLost: complaints.reduce((sum, c) => sum + c.amount_inr, 0),
  activeHotspots: predictions.filter((p) => p.risk_level === "critical").length,
  avgConfidence:
    predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length,
  fraudTypeBreakdown: FRAUD_TYPES.map((type) => ({
    type,
    count: complaints.filter((c) => c.fraud_type === type).length,
  })),
};
