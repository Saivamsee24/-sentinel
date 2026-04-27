# %% [markdown]
# # IEEE-CIS Fraud Detection — EDA
#
# Quick exploratory pass before training. Goal: spend 2 hours max here.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data")
pd.set_option("display.max_columns", 50)

# %%
txn = pd.read_csv(DATA_DIR / "train_transaction.csv")
ident = pd.read_csv(DATA_DIR / "train_identity.csv")
print(f"Transactions: {txn.shape}")
print(f"Identity:     {ident.shape}")

# %%
# Class balance
fraud_rate = txn["isFraud"].mean()
print(f"Fraud rate: {fraud_rate:.4%}  (very imbalanced — use scale_pos_weight)")

txn["isFraud"].value_counts().plot(kind="bar", title="Class distribution")
plt.show()

# %%
# Missing data
missing = txn.isna().mean().sort_values(ascending=False)
print("Top 10 most-missing columns:")
print(missing.head(10))

# Many V-features are heavily missing — XGBoost handles NaN natively, no imputation needed.

# %%
# Transaction amount distribution by class
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
txn[txn.isFraud == 0]["TransactionAmt"].clip(0, 500).hist(bins=50, ax=ax[0])
ax[0].set_title("Legit — amount")
txn[txn.isFraud == 1]["TransactionAmt"].clip(0, 500).hist(bins=50, ax=ax[1], color="red")
ax[1].set_title("Fraud — amount")
plt.show()

# %%
# Top product codes by fraud rate
fraud_by_product = txn.groupby("ProductCD")["isFraud"].agg(["mean", "count"])
print(fraud_by_product.sort_values("mean", ascending=False))

# %%
# Card type fraud rates
fraud_by_card = txn.groupby("card4")["isFraud"].agg(["mean", "count"])
print(fraud_by_card.sort_values("mean", ascending=False))

# %% [markdown]
# ## Takeaways
# 1. ~3.5% fraud rate — heavy imbalance, use `scale_pos_weight`.
# 2. Many V-columns >50% missing — XGBoost native NaN handling is fine.
# 3. Use the dataset's existing engineered features (V1-V339, C1-C14, D1-D15) directly.
# 4. Skip custom feature engineering for v1 — get the baseline shipping.
