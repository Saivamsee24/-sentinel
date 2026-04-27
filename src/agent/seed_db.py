"""Seed SQLite with synthetic customer history for the investigator agent.

Usage:
    python -m src.agent.seed_db
"""

from __future__ import annotations

import os
import random
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.getenv("SQLITE_PATH", "data/sentinel.db"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    amount REAL NOT NULL,
    ts INTEGER NOT NULL,
    is_fraud INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_customer ON transactions(customer_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_merchant ON transactions(merchant_id);
"""


def seed(n_customers: int = 50, n_merchants: int = 20, txns_per_customer: int = 30) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)
    con.execute("DELETE FROM transactions")  # idempotent

    rng = random.Random(42)
    now = int(time.time())
    rows = []
    txn_id = 0

    for c in range(n_customers):
        baseline = rng.uniform(20, 200)
        fraud_prone = rng.random() < 0.05
        for _ in range(txns_per_customer):
            txn_id += 1
            merchant = f"M-{rng.randint(1, n_merchants)}"
            amount = max(1.0, rng.gauss(baseline, baseline * 0.4))
            ts = now - rng.randint(0, 60 * 86400)
            is_fraud = 1 if (fraud_prone and rng.random() < 0.1) else 0
            rows.append((f"T-{txn_id:06d}", f"C-{c}", merchant, round(amount, 2), ts, is_fraud))

    con.executemany(
        "INSERT INTO transactions (transaction_id, customer_id, merchant_id, amount, ts, is_fraud) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    con.commit()
    con.close()
    print(f"✓ Seeded {len(rows)} transactions into {DB_PATH}")


if __name__ == "__main__":
    seed()
