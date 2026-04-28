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
  return (
    <section className="rounded-xl border border-border bg-card/70 p-5 shadow-lg shadow-black/20">
      <h2 className="text-lg font-semibold">Transaction</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Pick a sample payload or edit JSON directly.
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
