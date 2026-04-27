"""Request and response schemas for the fraud scoring API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """A single transaction to score.

    The IEEE-CIS dataset has 400+ columns. Rather than pin every field as a typed
    attribute, we accept a dict of feature_name -> value. The API will align it to
    the model's expected feature schema before predicting.
    """

    transaction_id: str = Field(..., description="Unique transaction identifier")
    amount: float = Field(..., description="Transaction amount (USD)", ge=0)
    customer_id: str | None = Field(None, description="Customer ID for history lookup")
    merchant_id: str | None = Field(None, description="Merchant ID for stats lookup")
    features: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw IEEE-CIS feature dict (V1, C1, D1, card4, ProductCD, ...)",
    )


class PredictionResponse(BaseModel):
    transaction_id: str
    fraud_score: float = Field(..., ge=0, le=1, description="Probability of fraud")
    is_fraud: bool = Field(..., description="True if score > threshold")
    threshold: float = Field(..., description="Decision threshold used")
    top_features: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top contributing features (name + SHAP-ish importance)",
    )
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
