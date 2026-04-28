import { ActivitySquare } from "lucide-react";

export function EmptyState() {
  return (
    <div className="mt-6 flex min-h-[340px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-background/30 p-6 text-center">
      <ActivitySquare className="h-10 w-10 text-muted-foreground" />
      <p className="mt-3 text-sm font-medium">No score yet</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        Choose a sample transaction and run "Score" to view fraud risk, or run "Score + Investigate" for a full AI report.
      </p>
    </div>
  );
}
