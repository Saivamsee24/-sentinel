"""Streamlit dashboard for Sentinel.

Run:
    streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import json
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Sentinel — Fraud Investigator", layout="wide")
st.title("🛡️ Sentinel")
st.caption("Real-time fraud scoring + AI investigator")

# Sidebar — API health
with st.sidebar:
    st.subheader("Service status")
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        h = r.json()
        st.success(f"API: {h['status']}")
        st.caption(f"Model loaded: {h['model_loaded']}")
        st.caption(f"Version: {h.get('model_version', '-')}")
    except Exception as e:
        st.error(f"API unreachable: {e}")
    st.divider()
    st.caption(f"API URL: `{API_URL}`")

# Sample payload
SAMPLE = {
    "transaction_id": "T-DEMO-001",
    "amount": 1250.50,
    "customer_id": "C-1",
    "merchant_id": "M-7",
    "features": {
        "TransactionAmt": 1250.50,
        "ProductCD": "W",
        "card4": "visa",
        "card6": "credit",
    },
}

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Transaction")
    payload_text = st.text_area(
        "Paste a transaction JSON",
        value=json.dumps(SAMPLE, indent=2),
        height=320,
    )
    score_btn = st.button("Score", type="primary", use_container_width=True)
    investigate_btn = st.button("Score + Investigate", use_container_width=True)

with col2:
    st.subheader("Result")
    if score_btn or investigate_btn:
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
            st.stop()

        endpoint = "/investigate" if investigate_btn else "/predict"
        try:
            with st.spinner(f"Calling {endpoint}..."):
                r = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=30)
            r.raise_for_status()
            result = r.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            st.stop()

        # Prediction display
        pred = result if endpoint == "/predict" else result["prediction"]
        score = pred["fraud_score"]
        is_fraud = pred["is_fraud"]

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Fraud Score", f"{score:.4f}")
        metric_col2.metric("Decision", "FRAUD" if is_fraud else "LEGITIMATE")

        if is_fraud:
            st.error(f"🚨 Fraud detected (threshold: {pred['threshold']})")
        else:
            st.success("✓ Looks legitimate")

        with st.expander("Top features", expanded=True):
            for f in pred.get("top_features", [])[:5]:
                st.write(f"- **{f['name']}** — importance {f['importance']:.4f} · value: `{f['value']}`")

        if endpoint == "/investigate":
            st.subheader("🔍 Investigation")
            inv = result.get("investigation", "")
            try:
                inv_data = json.loads(inv)
                st.json(inv_data)
            except (json.JSONDecodeError, TypeError):
                st.write(inv)
    else:
        st.info("Click **Score** or **Score + Investigate** to run.")
