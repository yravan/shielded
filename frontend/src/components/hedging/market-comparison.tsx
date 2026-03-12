"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { HedgeComparison } from "@/types";

interface MarketComparisonProps {
  comparisons: HedgeComparison[];
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; fill: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="text-xs">
          <span style={{ color: p.fill }}>{p.name}</span>:{" "}
          <span className="font-mono">${(p.value / 1000).toFixed(0)}k</span>
        </p>
      ))}
    </div>
  );
}

export function MarketComparison({ comparisons }: MarketComparisonProps) {
  const data = comparisons.slice(0, 6).map((c) => ({
    name: c.eventTitle.length > 25 ? c.eventTitle.slice(0, 25) + "..." : c.eventTitle,
    "PM Cost": c.predictionMarket.cost,
    "Traditional Cost": c.traditional.cost,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data} margin={{ top: 4, right: 4, bottom: 60, left: 4 }}>
        <XAxis
          dataKey="name"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 10, fill: "oklch(0.60 0.02 250)" }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: "oklch(0.60 0.02 250)" }}
          tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          width={55}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
        <Bar dataKey="PM Cost" fill="oklch(0.65 0.19 250)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Traditional Cost" fill="oklch(0.60 0.02 250)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
