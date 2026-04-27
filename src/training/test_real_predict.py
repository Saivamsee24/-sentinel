"""Pull a real fraud row from IEEE-CIS, send it to the API, see if it scores high."""
import json
import pandas as pd
import requests

# Load 10 fraud rows
df = pd.read_csv("data/train_transaction.csv", nrows=50_000)
fraud_rows = df[df["isFraud"] == 1].head(5)

for _, row in fraud_rows.iterrows():
    # Build features dict from the row, dropping target/id columns
    features = row.drop(["isFraud", "TransactionID"]).to_dict()
    # Replace NaN with None (JSON-serializable)
    features = {k: (None if pd.isna(v) else v) for k, v in features.items()}

    payload = {
        "transaction_id": str(row["TransactionID"]),
        "amount": float(row["TransactionAmt"]),
        "features": features,
    }
    r = requests.post("http://localhost:8000/predict", json=payload)
    result = r.json()
    print(f"  TxnID {result['transaction_id']}: score={result['fraud_score']:.4f}  "
          f"is_fraud={result['is_fraud']} (truth=1)")