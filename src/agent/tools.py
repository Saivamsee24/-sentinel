"""Tools the investigator agent can call. Backed by SQLite for dev simplicity.

In production these would hit DynamoDB / a feature store, but the interface stays the same.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("SQLITE_PATH", "data/sentinel.db"))


@contextmanager
def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def get_customer_history(customer_id: str, limit: int = 10) -> dict:
    """Recent transactions + aggregate stats for a customer.

    Args:
        customer_id: Customer identifier.
        limit: Number of recent transactions to return.

    Returns:
        Dict with `recent_transactions`, `txn_count_30d`, `avg_amount`, `fraud_count_lifetime`.
    """
    with _conn() as con:
        rows = con.execute(
            "SELECT transaction_id, amount, merchant_id, ts, is_fraud "
            "FROM transactions WHERE customer_id = ? "
            "ORDER BY ts DESC LIMIT ?",
            (customer_id, limit),
        ).fetchall()

        agg = con.execute(
            "SELECT COUNT(*) AS n, AVG(amount) AS avg_amt, "
            "SUM(is_fraud) AS fraud_n "
            "FROM transactions WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()

    return {
        "customer_id": customer_id,
        "recent_transactions": [dict(r) for r in rows],
        "txn_count_lifetime": agg["n"] if agg else 0,
        "avg_amount": float(agg["avg_amt"]) if agg and agg["avg_amt"] else 0.0,
        "fraud_count_lifetime": int(agg["fraud_n"]) if agg and agg["fraud_n"] else 0,
    }


def get_merchant_stats(merchant_id: str) -> dict:
    """Aggregate stats for a merchant (fraud rate, txn count, avg amount)."""
    with _conn() as con:
        agg = con.execute(
            "SELECT COUNT(*) AS n, AVG(amount) AS avg_amt, "
            "AVG(is_fraud) AS fraud_rate "
            "FROM transactions WHERE merchant_id = ?",
            (merchant_id,),
        ).fetchone()

    if not agg or agg["n"] == 0:
        return {"merchant_id": merchant_id, "known": False}

    return {
        "merchant_id": merchant_id,
        "known": True,
        "txn_count": agg["n"],
        "avg_amount": float(agg["avg_amt"] or 0),
        "fraud_rate": float(agg["fraud_rate"] or 0),
    }


def find_similar_transactions(amount: float, merchant_id: str | None, limit: int = 5) -> list[dict]:
    """Find transactions with similar amount at the same merchant — useful for context."""
    if not merchant_id:
        return []
    low, high = amount * 0.8, amount * 1.2
    with _conn() as con:
        rows = con.execute(
            "SELECT transaction_id, customer_id, amount, ts, is_fraud "
            "FROM transactions WHERE merchant_id = ? AND amount BETWEEN ? AND ? "
            "ORDER BY ts DESC LIMIT ?",
            (merchant_id, low, high, limit),
        ).fetchall()
    return [dict(r) for r in rows]
