import { Loader2 } from "lucide-react";

import type { InvestigationData, PredictResponse } from "../lib/api";
import { EmptyState } from "./EmptyState";
import { FeatureChart } from "./FeatureChart";
import { FraudGauge } from "./FraudGauge";
import { InvestigatorReport } from "./InvestigatorReport";
import { VerdictBadge } from "./VerdictBadge";

type ResultPanelProps = {
  title: string;
  loading: boolean;
  error: string | null;
  prediction: PredictResponse | null;
  investigation: InvestigationData | null;
};

export function ResultPanel({
  title,
  loading,
  error,
  prediction,
  investigation,
}: ResultPanelProps) {
  const hasResult = Boolean(prediction);

  return (
    <section className="rounded-xl border border-border bg-card/70 p-5 shadow-lg shadow-black/20">
      <h2 className="text-lg font-semibold">{title}</h2>

      {loading && (
        <div className="mt-6 flex min-h-[340px] items-center justify-center">
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Running model inference...</span>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          {error}
        </div>
      )}

      {!loading && !error && !hasResult && <EmptyState />}

      {!loading && !error && prediction && (
        <div className="mt-5 space-y-6">
          <div className="flex flex-col items-center gap-4">
            <FraudGauge score={prediction.fraud_score} />
            <VerdictBadge score={prediction.fraud_score} />
          </div>

          <div>
            <p className="mb-2 text-sm font-medium text-muted-foreground">Top Contributing Features</p>
            <FeatureChart features={prediction.top_features.slice(0, 5)} />
          </div>

          {investigation && <InvestigatorReport report={investigation} />}
        </div>
      )}
    </section>
  );
}
