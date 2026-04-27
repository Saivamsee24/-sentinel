"""Smoke tests for the API. Don't require a trained model — verify endpoints + schemas."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.schemas import Transaction


client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body


def test_transaction_schema_validation():
    txn = Transaction(transaction_id="T-1", amount=100.0, customer_id="C-1", merchant_id="M-1")
    assert txn.transaction_id == "T-1"
    assert txn.amount == 100.0


def test_predict_returns_503_when_no_model():
    """If model isn't loaded (e.g. CI without trained artifact), API responds gracefully."""
    r = client.post(
        "/predict",
        json={"transaction_id": "T-1", "amount": 100.0, "features": {}},
    )
    # Either 200 (model loaded) or 503 (not loaded) — both are valid responses.
    assert r.status_code in (200, 503)
