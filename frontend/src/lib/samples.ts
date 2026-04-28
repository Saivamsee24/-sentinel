import { CheckCircle2, Flag, TriangleAlert, type LucideIcon } from "lucide-react";

import type { TransactionPayload } from "./api";

export type SampleTransaction = {
  id: string;
  label: string;
  description: string;
  tone: "success" | "warning" | "danger";
  icon: LucideIcon;
  payload: TransactionPayload;
};

export const LOW_RISK_TRANSACTION: SampleTransaction = {
  id: "low-risk",
  label: "Low Risk",
  description: "Small everyday purchase ($45.20)",
  tone: "success",
  icon: CheckCircle2,
  payload: {
    transaction_id: "T-DEMO-LOW",
    amount: 45.2,
    customer_id: "C-1",
    merchant_id: "M-7",
    features: {
      TransactionAmt: 45.2,
      ProductCD: "W",
      card4: "visa",
      card6: "credit",
    },
  },
};

export const ANOMALOUS_AMOUNT_TRANSACTION: SampleTransaction = {
  id: "anomalous-amount",
  label: "Anomalous Amount",
  description: "$4500 purchase (24x customer baseline)",
  tone: "warning",
  icon: TriangleAlert,
  payload: {
    transaction_id: "T-DEMO-HIGH",
    amount: 4500.0,
    customer_id: "C-1",
    merchant_id: "M-7",
    features: {
      TransactionAmt: 4500.0,
      ProductCD: "W",
      card4: "visa",
      card6: "credit",
    },
  },
};

export const UNKNOWN_MERCHANT_TRANSACTION: SampleTransaction = {
  id: "unknown-merchant",
  label: "Unknown Merchant",
  description: "$850 cold-start risk",
  tone: "danger",
  icon: Flag,
  payload: {
    transaction_id: "T-DEMO-COLD",
    amount: 850.0,
    customer_id: "C-1",
    merchant_id: "M-UNKNOWN-99",
    features: {
      TransactionAmt: 850.0,
      ProductCD: "W",
      card4: "visa",
    },
  },
};

export const SAMPLE_TRANSACTIONS: SampleTransaction[] = [
  LOW_RISK_TRANSACTION,
  ANOMALOUS_AMOUNT_TRANSACTION,
  UNKNOWN_MERCHANT_TRANSACTION,
];
