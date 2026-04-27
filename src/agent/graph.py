"""LangGraph fraud investigator agent.

Linear graph: enrich → analyze → explain. No conditional edges, no retries.
Keep it simple — we're shipping in 2 days.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .tools import find_similar_transactions, get_customer_history, get_merchant_stats

log = logging.getLogger(__name__)

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class InvestigatorState(TypedDict):
    transaction: dict
    prediction: dict
    enrichment: dict
    analysis: dict
    explanation: str


# ---------- Nodes ----------

def enrich_node(state: InvestigatorState) -> dict:
    """Pull customer history + merchant stats + similar txns from SQLite."""
    txn = state["transaction"]
    customer_id = txn.get("customer_id")
    merchant_id = txn.get("merchant_id")
    amount = txn.get("amount", 0.0)

    enrichment = {
        "customer_history": get_customer_history(customer_id) if customer_id else {},
        "merchant_stats": get_merchant_stats(merchant_id) if merchant_id else {},
        "similar_transactions": find_similar_transactions(amount, merchant_id),
    }
    log.info(
        "Enriched: %d recent txns, merchant_known=%s",
        len(enrichment["customer_history"].get("recent_transactions", [])),
        enrichment["merchant_stats"].get("known", False),
    )
    return {"enrichment": enrichment}


def analyze_node(state: InvestigatorState) -> dict:
    """Compute simple risk signals from the enrichment."""
    txn = state["transaction"]
    enr = state["enrichment"]
    pred = state["prediction"]

    signals = []

    # Amount anomaly vs customer baseline
    avg = enr.get("customer_history", {}).get("avg_amount", 0)
    if avg > 0 and txn.get("amount", 0) > avg * 5:
        signals.append(f"Amount {txn['amount']:.2f} is {txn['amount']/avg:.1f}× customer average ({avg:.2f})")

    # Merchant reputation
    merchant = enr.get("merchant_stats", {})
    if merchant.get("known") and merchant.get("fraud_rate", 0) > 0.05:
        signals.append(f"Merchant has elevated fraud rate: {merchant['fraud_rate']:.1%}")
    elif not merchant.get("known"):
        signals.append("Merchant has no prior history (cold-start risk)")

    # Customer fraud history
    fraud_count = enr.get("customer_history", {}).get("fraud_count_lifetime", 0)
    if fraud_count > 0:
        signals.append(f"Customer has {fraud_count} prior fraud incident(s)")

    # Top model features
    top_features = pred.get("top_features", [])

    return {
        "analysis": {
            "risk_signals": signals,
            "top_features": top_features,
            "fraud_score": pred.get("fraud_score"),
        }
    }


def explain_node(state: InvestigatorState) -> dict:
    """Use Bedrock (Claude) to write a structured natural-language explanation.

    Falls back to a deterministic template if Bedrock isn't reachable — useful for
    local dev without AWS credentials.
    """
    txn = state["transaction"]
    pred = state["prediction"]
    analysis = state["analysis"]

    prompt = _build_prompt(txn, pred, analysis)

    explanation = _call_bedrock(prompt) or _fallback_explanation(analysis)
    return {"explanation": explanation}


def _build_prompt(txn: dict, pred: dict, analysis: dict) -> str:
    return f"""You are a fraud investigator. Analyze this transaction and produce a short, structured explanation.

Transaction:
{json.dumps({"id": txn.get("transaction_id"), "amount": txn.get("amount"), "customer": txn.get("customer_id"), "merchant": txn.get("merchant_id")}, indent=2)}

Model prediction:
- Fraud score: {pred.get("fraud_score"):.4f}
- Decision: {"FRAUD" if pred.get("is_fraud") else "LEGITIMATE"}

Risk signals from enrichment:
{json.dumps(analysis["risk_signals"], indent=2)}

Top model features:
{json.dumps(analysis["top_features"][:5], indent=2)}

Respond ONLY with valid JSON in this format:
{{
  "verdict": "fraud" | "legitimate" | "review",
  "confidence": "high" | "medium" | "low",
  "summary": "<one sentence>",
  "reasoning": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
  "recommended_action": "<one of: approve, review, block>"
}}
"""


def _call_bedrock(prompt: str) -> str | None:
    """Call AWS Bedrock. Returns None if AWS isn't available — caller falls back."""
    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )
        payload = json.loads(response["body"].read())
        return payload["content"][0]["text"]
    except Exception as e:
        log.warning("Bedrock call failed (%s); using fallback explanation.", e)
        return None


def _fallback_explanation(analysis: dict) -> str:
    """Deterministic template for local dev without Bedrock."""
    score = analysis.get("fraud_score") or 0.0
    if score > 0.8:
        verdict, action, conf = "fraud", "block", "high"
    elif score > 0.5:
        verdict, action, conf = "review", "review", "medium"
    else:
        verdict, action, conf = "legitimate", "approve", "high"

    return json.dumps(
        {
            "verdict": verdict,
            "confidence": conf,
            "summary": f"Model fraud score {score:.2f} with {len(analysis['risk_signals'])} risk signal(s).",
            "reasoning": analysis["risk_signals"][:3] or ["No anomalous signals from enrichment."],
            "recommended_action": action,
        },
        indent=2,
    )


# ---------- Graph ----------

def build_investigator():
    """Build and compile the 3-node investigator graph."""
    graph = StateGraph(InvestigatorState)
    graph.add_node("enrich", enrich_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("explain", explain_node)

    graph.add_edge(START, "enrich")
    graph.add_edge("enrich", "analyze")
    graph.add_edge("analyze", "explain")
    graph.add_edge("explain", END)

    return graph.compile()


if __name__ == "__main__":
    # Smoke test
    agent = build_investigator()
    result = agent.invoke(
        {
            "transaction": {
                "transaction_id": "T-001",
                "amount": 4500.0,
                "customer_id": "C-1",
                "merchant_id": "M-99",
            },
            "prediction": {
                "fraud_score": 0.87,
                "is_fraud": True,
                "top_features": [{"name": "TransactionAmt", "importance": 0.12, "value": 4500.0}],
            },
        }
    )
    print(result["explanation"])
