import { Shield } from "lucide-react";

import { StatusBadge } from "./StatusBadge";

export function Header() {
  return (
    <header className="rounded-xl border border-border bg-card/70 p-4 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="flex items-center gap-2 text-2xl font-semibold sm:text-3xl">
            <Shield className="h-8 w-8 text-primary" />
            <span>🛡️ Sentinel</span>
          </h1>
          <p className="max-w-3xl text-sm text-muted-foreground sm:text-base">
            AI-Powered Fraud Detection — XGBoost (0.97 AUC) + LangGraph + Bedrock
          </p>
        </div>

        <StatusBadge />
      </div>
    </header>
  );
}
