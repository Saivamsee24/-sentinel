import { cn } from "../lib/utils";
import type { SampleTransaction } from "../lib/samples";

type SampleCardProps = {
  sample: SampleTransaction;
  selected: boolean;
  onClick: () => void;
};

const toneStyles: Record<SampleTransaction["tone"], string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-200",
  danger: "border-red-500/30 bg-red-500/10 text-red-200",
};

export function SampleCard({ sample, selected, onClick }: SampleCardProps) {
  const Icon = sample.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full rounded-lg border p-3 text-left transition-all duration-200",
        "hover:-translate-y-0.5 hover:shadow-md hover:shadow-black/20",
        selected ? toneStyles[sample.tone] : "border-border bg-card text-foreground"
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className={cn("mt-0.5 h-5 w-5", selected ? "" : "text-muted-foreground")} />
        <div>
          <p className="text-sm font-semibold">{sample.label}</p>
          <p className="mt-1 text-xs text-muted-foreground">{sample.description}</p>
        </div>
      </div>
    </button>
  );
}
