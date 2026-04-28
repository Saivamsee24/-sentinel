import { useMemo, useState } from "react";

import { Header } from "./components/Header";
import { ResultPanel } from "./components/ResultPanel";
import { TransactionPanel } from "./components/TransactionPanel";
import {
  ApiRequestError,
  investigateTransaction,
  predictTransaction,
  type InvestigationResponse,
  type PredictResponse,
  type TransactionPayload,
} from "./lib/api";
import {
  LOW_RISK_TRANSACTION,
  SAMPLE_TRANSACTIONS,
  type SampleTransaction,
} from "./lib/samples";

const COLD_START_ERROR =
  "The API may be waking up from cold start. Please wait about 30 seconds and try again.";

type ResultState = {
  loading: boolean;
  error: string | null;
  prediction: PredictResponse | null;
  investigation: InvestigationResponse["investigation"] | null;
};

const initialJson = JSON.stringify(LOW_RISK_TRANSACTION.payload, null, 2);

function App() {
  const [selectedSample, setSelectedSample] = useState<SampleTransaction>(LOW_RISK_TRANSACTION);
  const [transactionJson, setTransactionJson] = useState<string>(initialJson);
  const [result, setResult] = useState<ResultState>({
    loading: false,
    error: null,
    prediction: null,
    investigation: null,
  });

  const footerGithubUrl = "https://github.com/your-username/sentinel-fraud-demo";

  const scoreOnly = async () => {
    await runScoring(false);
  };

  const scoreAndInvestigate = async () => {
    await runScoring(true);
  };

  const handleSampleSelect = (sample: SampleTransaction) => {
    setSelectedSample(sample);
    setTransactionJson(JSON.stringify(sample.payload, null, 2));
  };

  const runScoring = async (withInvestigation: boolean) => {
    let payload: TransactionPayload;

    try {
      payload = JSON.parse(transactionJson) as TransactionPayload;
    } catch {
      setResult((prev) => ({
        ...prev,
        loading: false,
        error: "Invalid JSON. Please fix the transaction payload and try again.",
      }));
      return;
    }

    setResult({
      loading: true,
      error: null,
      prediction: null,
      investigation: null,
    });

    try {
      if (withInvestigation) {
        const investigationResponse = await investigateTransaction(payload);
        setResult({
          loading: false,
          error: null,
          prediction: investigationResponse.prediction,
          investigation: investigationResponse.investigation,
        });
        return;
      }

      const predictionResponse = await predictTransaction(payload);
      setResult({
        loading: false,
        error: null,
        prediction: predictionResponse,
        investigation: null,
      });
    } catch (error) {
      const friendlyMessage =
        error instanceof ApiRequestError
          ? error.message
          : "We could not reach the fraud API right now. Please try again.";

      const timeoutHint = friendlyMessage.toLowerCase().includes("timeout")
        ? `${friendlyMessage} ${COLD_START_ERROR}`
        : friendlyMessage;

      setResult({
        loading: false,
        error: timeoutHint,
        prediction: null,
        investigation: null,
      });
    }
  };

  const disableActions = result.loading;

  const resultTitle = useMemo(() => {
    if (result.loading) return "Scoring transaction...";
    return "Result";
  }, [result.loading]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <Header />

        <main className="mt-6 grid flex-1 gap-6 lg:grid-cols-2">
          <TransactionPanel
            selectedSampleId={selectedSample.id}
            samples={SAMPLE_TRANSACTIONS}
            transactionJson={transactionJson}
            onTransactionJsonChange={setTransactionJson}
            onSampleSelect={handleSampleSelect}
            onScore={scoreOnly}
            onScoreAndInvestigate={scoreAndInvestigate}
            disabled={disableActions}
          />

          <ResultPanel
            title={resultTitle}
            loading={result.loading}
            error={result.error}
            prediction={result.prediction}
            investigation={result.investigation}
          />
        </main>

        <footer className="mt-8 border-t border-border pt-4 text-xs text-muted-foreground">
          Built with FastAPI · XGBoost · LangGraph · Vite · Tailwind.{" "}
          <a
            href={footerGithubUrl}
            target="_blank"
            rel="noreferrer"
            className="text-primary transition-colors hover:text-primary/80"
          >
            View on GitHub
          </a>
          .
        </footer>
      </div>
    </div>
  );
}

export default App;
