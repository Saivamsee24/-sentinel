import type { InvestigationData } from "../lib/api";

type InvestigatorReportProps = {
  report: InvestigationData;
};

export function InvestigatorReport({ report }: InvestigatorReportProps) {
  return (
    <section className="rounded-lg border border-border bg-background/50 p-4">
      <h3 className="text-base font-semibold">Investigator's Report</h3>

      <div className="mt-3 grid gap-2 text-sm">
        <p>
          <span className="text-muted-foreground">Verdict:</span> {report.verdict}
        </p>
        <p>
          <span className="text-muted-foreground">Confidence:</span>{" "}
          {Math.round(report.confidence * 100)}%
        </p>
        <p>
          <span className="text-muted-foreground">Summary:</span> {report.summary}
        </p>

        <div>
          <p className="text-muted-foreground">Reasoning:</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {report.reasoning.map((reason, index) => (
              <li key={`${reason}-${index}`}>{reason}</li>
            ))}
          </ul>
        </div>

        <p>
          <span className="text-muted-foreground">Recommended action:</span> {report.recommended_action}
        </p>
      </div>
    </section>
  );
}
