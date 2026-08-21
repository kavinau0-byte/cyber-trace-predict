"""
Task 3 — NLP Entity Extraction
Takes raw complaint text (as a victim would actually type it) and extracts:
  1. Bank name        -> spaCy PhraseMatcher (rule-based, matches known bank names)
  2. Fraud type        -> trained ML classifier (TF-IDF + Logistic Regression),
                          trained on your synthetic_complaints.csv labels

Amount is NOT extracted here on purpose — real complaint forms usually have a
separate numeric "amount lost" field alongside the free-text description, so
that comes straight from the form, not from NLP.
"""

import csv
import json
import joblib
import spacy
from spacy.matcher import PhraseMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

DATA_FILE = "data/synthetic_complaints.csv"
MODEL_FILE = "ml/fraud_type_classifier.joblib"

BANKS = ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Bank of Baroda",
         "Punjab National Bank", "Kotak Mahindra Bank", "Canara Bank"]

nlp = spacy.load("en_core_web_sm")


def build_bank_matcher():
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(bank) for bank in BANKS]
    matcher.add("BANK", patterns)
    return matcher


BANK_MATCHER = build_bank_matcher()


def extract_bank(text):
    doc = nlp(text)
    matches = BANK_MATCHER(doc)
    if not matches:
        return None
    # take the longest match (handles "SBI" vs "State Bank" overlaps if extended later)
    spans = [doc[start:end] for _, start, end in matches]
    best = max(spans, key=lambda s: len(s.text))
    return best.text


def load_training_data():
    texts, labels = [], []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["complaint_text"])
            labels.append(row["fraud_type"])
    return texts, labels


def train_fraud_classifier():
    texts, labels = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print("=== Fraud Type Classifier — Test Set Performance ===")
    print(classification_report(y_test, preds))

    joblib.dump(pipeline, MODEL_FILE)
    print(f"Model saved -> {MODEL_FILE}")
    return pipeline


def load_or_train_classifier():
    try:
        return joblib.load(MODEL_FILE)
    except FileNotFoundError:
        print("No saved model found — training a new one...")
        return train_fraud_classifier()


def extract_entities(text, classifier):
    bank = extract_bank(text)
    fraud_type = classifier.predict([text])[0]
    proba = classifier.predict_proba([text])[0]
    confidence = round(max(proba), 3)

    return {
        "extracted_bank": bank,
        "extracted_fraud_type": fraud_type,
        "fraud_type_confidence": confidence,
    }


def demo():
    classifier = load_or_train_classifier()

    print("\n=== Demo 1: Extraction on an existing synthetic complaint ===")
    texts, labels = load_training_data()
    sample_text, actual_label = texts[0], labels[0]
    result = extract_entities(sample_text, classifier)
    print(f"Text: {sample_text}")
    print(f"Actual fraud type: {actual_label}")
    print(f"Extracted: {json.dumps(result, indent=2)}")

    print("\n=== Demo 2: Extraction on a brand-new, hand-written complaint ===")
    new_text = ("Someone called me pretending to be from ICICI Bank and asked me "
                "to share my OTP to 'verify' my card. Right after, ₹15,000 was "
                "deducted from my account.")
    result2 = extract_entities(new_text, classifier)
    print(f"Text: {new_text}")
    print(f"Extracted: {json.dumps(result2, indent=2)}")


if __name__ == "__main__":
    demo()