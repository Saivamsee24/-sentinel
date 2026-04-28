import { useEffect, useMemo, useState } from "react";

type FraudGaugeProps = {
  score: number;
};

function scoreColor(score: number) {
  if (score < 0.3) return "hsl(var(--success))";
  if (score <= 0.7) return "hsl(var(--warning))";
  return "hsl(var(--danger))";
}

export function FraudGauge({ score }: FraudGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    let raf = 0;
    const duration = 900;
    const start = performance.now();

    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      setAnimatedScore(score * progress);
      if (progress < 1) {
        raf = requestAnimationFrame(tick);
      }
    };

    setAnimatedScore(0);
    raf = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(raf);
  }, [score]);

  const radius = 68;
  const strokeWidth = 12;
  const normalizedRadius = radius - strokeWidth * 0.5;
  const circumference = 2 * Math.PI * normalizedRadius;

  const dashOffset = useMemo(() => {
    const clamped = Math.max(0, Math.min(animatedScore, 1));
    return circumference * (1 - clamped);
  }, [animatedScore, circumference]);

  const color = scoreColor(animatedScore);

  return (
    <div className="relative flex h-44 w-44 items-center justify-center">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 160 160" role="img" aria-label="Fraud score gauge">
        <circle
          cx="80"
          cy="80"
          r={normalizedRadius}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth={strokeWidth}
        />
        <circle
          cx="80"
          cy="80"
          r={normalizedRadius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 100ms linear" }}
        />
      </svg>

      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold">{Math.round(animatedScore * 100)}%</span>
        <span className="text-xs uppercase tracking-wide text-muted-foreground">fraud score</span>
      </div>
    </div>
  );
}
