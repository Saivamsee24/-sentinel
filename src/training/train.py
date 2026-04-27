"""
Train an XGBoost fraud-detection model on the IEEE-CIS dataset.

Usage:
    python -m src.training.train

Expects:
    data/train_transaction.csv
    data/train_identity.csv

Produces:
    models/xgb_fraud.joblib
    models/feature_names.json
    models/metrics.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Tuple
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path("data")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

# DEVICE: "cuda" for GPU, "cpu" for CPU, or "auto" to detect.
# Override from CLI: TRAIN_DEVICE=cpu python -m src.training.train
DEVICE = os.getenv("TRAIN_DEVICE", "auto")

def load_data() -> pd.DataFrame:
    """Load and merge transaction + identity tables from IEEE-CIS."""
    txn_path = DATA_DIR / "train_transaction.csv"
    id_path = DATA_DIR / "train_identity.csv"

    if not txn_path.exists():
        raise FileNotFoundError(
            f"Missing {txn_path}. Download IEEE-CIS from Kaggle:\n"
            f"  kaggle competitions download -c ieee-fraud-detection -p data/"
        )

    log.info("Loading transaction data...")
    txn = pd.read_csv(txn_path)
    log.info("Loaded %d transactions, %d columns", len(txn), txn.shape[1])

    if id_path.exists():
        log.info("Loading identity data...")
        ident = pd.read_csv(id_path)
        df = txn.merge(ident, on="TransactionID", how="left")
        log.info("Merged: %d rows, %d cols", len(df), df.shape[1])
    else:
        log.warning("No identity file — proceeding with transactions only.")
        df = txn

    return df


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list[str]]:
    """Light feature prep: drop ID, label-encode categoricals, leave NaNs (XGBoost handles them)."""
    y = df["isFraud"].astype(int)
    X = df.drop(columns=["isFraud", "TransactionID"], errors="ignore")

    # XGBoost native categorical support (xgboost >= 2.0)
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    for c in cat_cols:
        X[c] = X[c].astype("category")

    log.info("Features: %d (%d categorical)", X.shape[1], len(cat_cols))
    return X, y, X.columns.tolist()

def _resolve_device() -> str:
    """Resolve the training device. Returns 'cuda' or 'cpu'.

    Auto-detects by trying a tiny GPU fit; falls back to CPU on any failure.
    Use TRAIN_DEVICE=cpu to force CPU even if a GPU is available.
    """
    if DEVICE == "cpu":
        log.info("Device: CPU (forced via TRAIN_DEVICE)")
        return "cpu"
    if DEVICE == "cuda":
        log.info("Device: CUDA (forced via TRAIN_DEVICE)")
        return "cuda"

    # Auto-detect
    try:
        from sklearn.datasets import make_classification

        Xs, ys = make_classification(n_samples=200, n_features=10, random_state=0)
        XGBClassifier(n_estimators=2, device="cuda", verbosity=0).fit(Xs, ys)
        log.info("Device: CUDA (auto-detected)")
        return "cuda"
    except Exception as e:
        log.info("Device: CPU (no usable GPU — %s)", str(e).split("\n")[0])
        return "cpu"


def train_model(X_train, y_train, X_val, y_val, device: str = "cpu") -> XGBClassifier:
    """XGBoost with sane defaults + light tuning. Target: 0.92+ AUC.

    Args:
        device: "cuda" for GPU, "cpu" for CPU. The trained model is converted
                to CPU before being returned, so it's portable to CPU-only
                production containers (no device-mismatch warning at inference).
    """
    pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    log.info("Class imbalance — scale_pos_weight=%.2f", pos_weight)
    log.info("Training device: %s", device)

    model = XGBClassifier(
        n_estimators=600,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        scale_pos_weight=pos_weight,
        tree_method="hist",
        device=device,
        enable_categorical=True,
        eval_metric="auc",
        early_stopping_rounds=30,
        random_state=42,
        n_jobs=-1,
    )

    log.info("Training XGBoost...")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)

    # Move the trained booster to CPU so the saved model loads cleanly on
    # CPU-only production containers (ECS Fargate). This kills the
    # "mismatched devices" warning at inference time.
    if device == "cuda":
        log.info("Converting model to CPU for portability...")
        model.get_booster().set_param({"device": "cpu"})

    return model

def evaluate(model: XGBClassifier, X_val, y_val) -> dict:
    """Compute AUC + PR-AUC on validation set."""
    proba = model.predict_proba(X_val)[:, 1]
    metrics = {
        "auc": float(roc_auc_score(y_val, proba)),
        "pr_auc": float(average_precision_score(y_val, proba)),
        "n_val": int(len(y_val)),
        "n_features": int(X_val.shape[1]),
    }
    log.info("AUC=%.4f | PR-AUC=%.4f", metrics["auc"], metrics["pr_auc"])
    return metrics


def main() -> None:
    df = load_data()
    X, y, feature_names = prepare_features(df)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    log.info("Train=%d, Val=%d", len(X_train), len(X_val))

    device = _resolve_device()
    model = train_model(X_train, y_train, X_val, y_val, device=device)
    metrics = evaluate(model, X_val, y_val)

    # Save artifacts
    model_path = MODEL_DIR / "xgb_fraud.joblib"
    joblib.dump(model, model_path)
    log.info("Saved model → %s", model_path)

# Save full schema: column order, dtypes, and category levels for each
    # categorical column. This is what the API needs to reproduce the exact
    # input format the model was trained on. Without this, categorical encoding
    # at inference is meaningless and predictions silently degrade.
    schema = {
        "feature_names": feature_names,
        "dtypes": {col: str(X_train[col].dtype) for col in feature_names},
        "categories": {
            col: X_train[col].cat.categories.tolist()
            for col in feature_names
            if str(X_train[col].dtype) == "category"
        },
    }
    (MODEL_DIR / "feature_schema.json").write_text(
        json.dumps(schema, indent=2, default=str)
    )
    # Keep these for backward compatibility
    (MODEL_DIR / "feature_names.json").write_text(json.dumps(feature_names, indent=2))
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    log.info("Saved feature names + metrics")

    if metrics["auc"] < 0.92:
        log.warning("AUC %.4f below 0.92 target — consider light tuning.", metrics["auc"])
    else:
        log.info("✓ Target AUC achieved.")


if __name__ == "__main__":
    main()
