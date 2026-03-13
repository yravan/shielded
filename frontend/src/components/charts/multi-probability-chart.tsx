"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ProbabilityPoint } from "@/types";

const LINE_COLORS = [
  "#3b82f6", // blue
  "#ef4444", // red
  "#10b981", // emerald
  "#f59e0b", // amber
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#f97316", // orange
  "#6366f1", // indigo
  "#14b8a6", // teal
];

interface MarketLine {
  id: string;
  title: string;
  probability: number;
  history: ProbabilityPoint[];
}

interface MultiProbabilityChartProps {
  markets: MarketLine[];
  height?: number;
  maxLines?: number;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function MultiTooltip({ active, payload, label, markets }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg max-w-xs">
      <p className="text-xs text-muted-foreground mb-1">
        {(() => { const d = new Date(label); return `${d.getMonth() + 1}/${d.getDate()}`; })()}
      </p>
      {payload.map((entry: any) => {
        const market = (markets ?? []).find((m: MarketLine) => m.id === entry.dataKey);
        return (
          <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: entry.color }}
            />
            <span className="truncate">{market?.title ?? entry.dataKey}</span>
            <span className="font-mono font-semibold ml-auto">
              {(entry.value * 100).toFixed(1)}%
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function MultiProbabilityChart({
  markets,
  height = 350,
  maxLines = 5,
}: MultiProbabilityChartProps) {
  // Take top N markets by probability
  const visibleMarkets = markets.slice(0, maxLines);

  if (visibleMarkets.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground text-sm"
        style={{ height }}
      >
        No market data available
      </div>
    );
  }

  // Build unified data array: { date, [marketTitle]: probability }
  // Collect all unique timestamps across all markets
  const dateMap = new Map<string, Record<string, number>>();

  for (const market of visibleMarkets) {
    for (const point of market.history) {
      const dateKey = point.date;
      if (!dateMap.has(dateKey)) {
        dateMap.set(dateKey, {});
      }
      dateMap.get(dateKey)![market.id] = point.probability;
    }
  }

  // Sort by date and build chart data
  const chartData = Array.from(dateMap.entries())
    .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
    .map(([date, values]) => ({
      date,
      ...values,
    }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <XAxis
          dataKey="date"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          tickFormatter={(v) => {
            const d = new Date(v);
            return `${d.getMonth() + 1}/${d.getDate()}`;
          }}
          minTickGap={40}
        />
        <YAxis
          domain={["auto", "auto"]}
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          width={45}
        />
        <Tooltip content={<MultiTooltip markets={visibleMarkets} />} />
        <Legend
          formatter={(value: string) => {
            const market = visibleMarkets.find((m) => m.id === value);
            if (!market) return value;
            return `${market.title} (${(market.probability * 100).toFixed(0)}%)`;
          }}
          wrapperStyle={{ fontSize: "12px" }}
        />
        {visibleMarkets.map((market, index) => (
          <Line
            key={market.id}
            type="monotone"
            dataKey={market.id}
            name={market.id}
            stroke={LINE_COLORS[index % LINE_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
