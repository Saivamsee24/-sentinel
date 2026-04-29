import { useEffect, useState } from "react";

import {
  AMOUNT_UNIT,
  CARD4_OPTIONS,
  CARD6_OPTIONS,
  PRODUCT_CD_OPTIONS,
} from "../lib/featureOptions";
import type { TransactionPayload } from "../lib/api";
import type { SampleTransaction } from "../lib/samples";
import { SampleCard } from "./SampleCard";

type TransactionPanelProps = {
  selectedSampleId: string;
  samples: SampleTransaction[];
  transactionJson: string;
  disabled: boolean;
  onTransactionJsonChange: (value: string) => void;
  onSampleSelect: (sample: SampleTransaction) => void;
  onScore: () => void;
  onScoreAndInvestigate: () => void;
};

export function TransactionPanel({
  selectedSampleId,
  samples,
  transactionJson,
  disabled,
  onTransactionJsonChange,
  onSampleSelect,
  onScore,
  onScoreAndInvestigate,
}: TransactionPanelProps) {
  const [form, setForm] = useState({
    transactionId: "T-DEMO-LOW",
    amount: 45.2,
    customerId: "C-1",
    merchantId: "M-7",
    productCd: "W",
    card4: "visa",
    card6: "credit",
  });

  useEffect(() => {
    try {
      const parsed = JSON.parse(transactionJson) as TransactionPayload;
      setForm({
        transactionId: parsed.transaction_id ?? "T-DEMO-LOW",
        amount: Number(parsed.amount ?? 0),
        customerId: parsed.customer_id ?? "C-1",
        merchantId: parsed.merchant_id ?? "M-7",
        productCd: String(parsed.features?.ProductCD ?? "W"),
        card4: String(parsed.features?.card4 ?? "visa"),
        card6: String(parsed.features?.card6 ?? "credit"),
      });
    } catch {
      // Keep form as-is while user edits invalid JSON manually.
    }
  }, [transactionJson]);

  const updateJsonFromForm = (nextForm: typeof form) => {
    const payload: TransactionPayload = {
      transaction_id: nextForm.transactionId.trim() || "T-DEMO-CUSTOM",
      amount: Number.isFinite(nextForm.amount) ? Number(nextForm.amount) : 0,
      customer_id: nextForm.customerId.trim() || "C-1",
      merchant_id: nextForm.merchantId.trim() || "M-1",
      features: {
        TransactionAmt: Number.isFinite(nextForm.amount) ? Number(nextForm.amount) : 0,
        ProductCD: nextForm.productCd,
        card4: nextForm.card4,
        card6: nextForm.card6,
      },
    };
    onTransactionJsonChange(JSON.stringify(payload, null, 2));
  };

  const handleFormUpdate = (patch: Partial<typeof form>) => {
    const next = { ...form, ...patch };
    setForm(next);
    updateJsonFromForm(next);
  };

  return (
    <section className="rounded-xl border border-border bg-card/70 p-5 shadow-lg shadow-black/20">
      <h2 className="text-lg font-semibold">Transaction</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Pick a sample payload, use guided inputs, or edit JSON directly.
      </p>

      <div className="mt-4 space-y-3">
        {samples.map((sample) => (
          <SampleCard
            key={sample.id}
            sample={sample}
            selected={sample.id === selectedSampleId}
            onClick={() => onSampleSelect(sample)}
          />
        ))}
      </div>

      <div className="mt-4 rounded-lg border border-input bg-background/40 p-3">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Quick Input (dataset-based options)
        </p>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-muted-foreground">
            Transaction ID
            <input
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.transactionId}
              onChange={(event) => handleFormUpdate({ transactionId: event.target.value })}
              disabled={disabled}
            />
          </label>

          <label className="text-xs text-muted-foreground">
            Amount ({AMOUNT_UNIT})
            <input
              type="number"
              step="0.01"
              min="0"
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={Number.isNaN(form.amount) ? "" : form.amount}
              onChange={(event) => handleFormUpdate({ amount: Number(event.target.value) })}
              disabled={disabled}
            />
          </label>

          <label className="text-xs text-muted-foreground">
            Customer ID
            <input
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.customerId}
              onChange={(event) => handleFormUpdate({ customerId: event.target.value })}
              disabled={disabled}
            />
          </label>

          <label className="text-xs text-muted-foreground">
            Merchant ID
            <input
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.merchantId}
              onChange={(event) => handleFormUpdate({ merchantId: event.target.value })}
              disabled={disabled}
            />
          </label>

          <label className="text-xs text-muted-foreground">
            ProductCD
            <select
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.productCd}
              onChange={(event) => handleFormUpdate({ productCd: event.target.value })}
              disabled={disabled}
            >
              {PRODUCT_CD_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="text-xs text-muted-foreground">
            Card Network (card4)
            <select
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.card4}
              onChange={(event) => handleFormUpdate({ card4: event.target.value })}
              disabled={disabled}
            >
              {CARD4_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label className="text-xs text-muted-foreground sm:col-span-2">
            Card Type (card6)
            <select
              className="mt-1 w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground outline-none ring-primary/40 focus:ring-2"
              value={form.card6}
              onChange={(event) => handleFormUpdate({ card6: event.target.value })}
              disabled={disabled}
            >
              {CARD6_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="mt-4">
        <label htmlFor="transaction-json" className="mb-2 block text-xs font-medium text-muted-foreground">
          Transaction JSON
        </label>
        <textarea
          id="transaction-json"
          className="min-h-[220px] w-full rounded-lg border border-input bg-background/60 p-3 text-sm text-foreground outline-none ring-primary/40 transition focus:ring-2"
          value={transactionJson}
          onChange={(event) => onTransactionJsonChange(event.target.value)}
          spellCheck={false}
          disabled={disabled}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={onScore}
          disabled={disabled}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Score
        </button>
        <button
          type="button"
          onClick={onScoreAndInvestigate}
          disabled={disabled}
          className="rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Score + Investigate
        </button>
      </div>
    </section>
  );
}
