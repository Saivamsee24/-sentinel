"""FastAPI inference service for the Sentinel fraud detection model."""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import HealthResponse, PredictionResponse, Transaction

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/xgb_fraud.joblib"))
FEATURES_PATH = Path("models/feature_names.json")
THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.5"))
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Module-level state. Loaded once at startup.
_state: dict = {"model": None, "features": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, free on shutdown."""
    log.info("Loading model from %s", MODEL_PATH)
    if not MODEL_PATH.exists():
        log.error("Model file not found. Run `python -m src.training.train` first.")
    else:
        _state["model"] = joblib.load(MODEL_PATH)
        schema_path = Path("models/feature_schema.json")
        if schema_path.exists():
            _state["schema"] = json.loads(schema_path.read_text())
            _state["features"] = _state["schema"]["feature_names"]
            log.info(
                "Model loaded. %d features expected (%d categorical).",
                len(_state["features"]),
                len(_state["schema"].get("categories", {})),
            )
        elif FEATURES_PATH.exists():
            _state["features"] = json.loads(FEATURES_PATH.read_text())
            _state["schema"] = None
            log.warning("Loaded feature_names only — no schema. Categorical encoding may be wrong.")
        else:
            log.warning("No feature schema found. Predictions may be unreliable.")
    yield
    _state.clear()
    log.info("Model unloaded.")


app = FastAPI(
    title="Sentinel Fraud API",
    description="Real-time fraud scoring backed by XGBoost on IEEE-CIS.",
    version=MODEL_VERSION,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_feature_frame(txn: Transaction) -> pd.DataFrame:
    """Align incoming feature dict to the EXACT schema the model was trained on.

    Reproduces the training feature DataFrame's column order, dtypes, and
    categorical levels (so integer codes match training). Without this,
    a 0.96 AUC model produces ~0.10 fraud scores on real fraud rows.
    """
    expected = _state["features"]
    schema = _state.get("schema")

    if expected is None:
        return pd.DataFrame([txn.features])

    features = dict(txn.features)
    if "TransactionAmt" in expected and "TransactionAmt" not in features:
        features["TransactionAmt"] = txn.amount

    row = {col: features.get(col, np.nan) for col in expected}
    df = pd.DataFrame([row], columns=expected)

    if schema is None:
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype("category")
        return df

    dtypes = schema["dtypes"]
    categories = schema.get("categories", {})

    for col in expected:
        target_dtype = dtypes.get(col, "float64")

        if target_dtype == "category":
            cat_dtype = pd.CategoricalDtype(categories=categories[col])
            df[col] = pd.Categorical(df[col], dtype=cat_dtype)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if "float" in target_dtype:
                df[col] = df[col].astype(target_dtype)
            elif "int" in target_dtype and not df[col].isna().any():
                df[col] = df[col].astype(target_dtype)

    return df

def _top_features(model, X: pd.DataFrame, k: int = 5) -> list[dict]:
    """Cheap feature attribution: combine model's global importance with present-feature values."""
    importance = getattr(model, "feature_importances_", None)
    if importance is None:
        return []
    cols = X.columns.tolist()
    pairs = sorted(zip(cols, importance), key=lambda p: p[1], reverse=True)[:k]
    out = []
    for name, imp in pairs:
        val = X.iloc[0][name]
        if isinstance(val, float) and np.isnan(val):
            val = None
        out.append({"name": name, "importance": float(imp), "value": val})
    return out


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=_state["model"] is not None,
        model_version=MODEL_VERSION if _state["model"] else None,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(txn: Transaction) -> PredictionResponse:
    if _state["model"] is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        X = _build_feature_frame(txn)
        proba = float(_state["model"].predict_proba(X)[0, 1])
    except Exception as e:
        log.exception("Inference failed for %s", txn.transaction_id)
        raise HTTPException(status_code=400, detail=f"Inference error: {e}")

    return PredictionResponse(
        transaction_id=txn.transaction_id,
        fraud_score=proba,
        is_fraud=proba >= THRESHOLD,
        threshold=THRESHOLD,
        top_features=_top_features(_state["model"], X),
        model_version=MODEL_VERSION,
    )


@app.post("/investigate")
async def investigate(txn: Transaction):
    """Run the LangGraph investigator agent for an explanation.

    Lazy-imports the agent so the API can boot without LangGraph deps available.
    """
    if _state["model"] is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Score first
    pred = await predict(txn)

    # Then investigate
    try:
        from src.agent.graph import build_investigator

        agent = build_investigator()
        result = agent.invoke(
            {
                "transaction": txn.model_dump(),
                "prediction": pred.model_dump(),
            }
        )
        return {"prediction": pred.model_dump(), "investigation": result.get("explanation")}
    except Exception as e:
        log.exception("Investigation failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
