"""Tests for the investigator agent's pure logic (no AWS required)."""

from __future__ import annotations

import json

from src.agent.graph import _fallback_explanation, analyze_node


def test_analyze_flags_high_amount():
    state = {
        "transaction": {"amount": 5000.0, "customer_id": "C-1", "merchant_id": "M-1"},
        "prediction": {"fraud_score": 0.9, "top_features": []},
        "enrichment": {
            "customer_history": {"avg_amount": 100.0, "fraud_count_lifetime": 0},
            "merchant_stats": {"known": True, "fraud_rate": 0.01},
            "similar_transactions": [],
        },
    }
    out = analyze_node(state)
    signals = out["analysis"]["risk_signals"]
    assert any("average" in s.lower() for s in signals)


def test_fallback_explanation_is_valid_json():
    analysis = {"fraud_score": 0.85, "risk_signals": ["high amount"], "top_features": []}
    text = _fallback_explanation(analysis)
    data = json.loads(text)
    assert data["verdict"] == "fraud"
    assert data["recommended_action"] == "block"


def test_fallback_explanation_legitimate():
    analysis = {"fraud_score": 0.1, "risk_signals": [], "top_features": []}
    data = json.loads(_fallback_explanation(analysis))
    assert data["verdict"] == "legitimate"
    assert data["recommended_action"] == "approve"
