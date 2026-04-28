import { ResponsiveContainer, Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import type { TopFeature } from "../lib/api";

type FeatureChartProps = {
  features: TopFeature[];
};

export function FeatureChart({ features }: FeatureChartProps) {
  return (
    <div className="h-64 w-full rounded-lg border border-border bg-background/40 p-3">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={features} layout="vertical" margin={{ top: 6, right: 14, left: 18, bottom: 6 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis type="number" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
          />
          <Tooltip
            cursor={{ fill: "hsl(var(--accent))" }}
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              borderColor: "hsl(var(--border))",
              color: "hsl(var(--foreground))",
              borderRadius: "0.5rem",
            }}
          />
          <Bar dataKey="importance" fill="hsl(var(--primary))" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
