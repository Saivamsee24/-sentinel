import { cn } from "../lib/utils";

type VerdictBadgeProps = {
  score: number;
};

function getVerdict(score: number) {
  if (score < 0.3) {
    return {
      label: "✓ APPROVE",
      styles: "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
    };
  }

  if (score <= 0.7) {
    return {
      label: "⚠ REVIEW",
      styles: "border-amber-500/40 bg-amber-500/10 text-amber-300",
    };
  }

  return {
    label: "🚫 BLOCK",
    styles: "border-red-500/40 bg-red-500/10 text-red-300",
  };
}

export function VerdictBadge({ score }: VerdictBadgeProps) {
  const verdict = getVerdict(score);

  return (
    <div className={cn("rounded-full border px-5 py-2 text-sm font-semibold tracking-wide", verdict.styles)}>
      {verdict.label}
    </div>
  );
}
