"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { EVPoint } from "@/lib/ev";

interface EVChartProps {
  data: EVPoint[];
  height?: number;
}

function formatValue(v: number): string {
  if (Math.abs(v) >= 1_000_000_000_000) return `$${(v / 1_000_000_000_000).toFixed(1)}T`;
  if (Math.abs(v) >= 1_000_000_000) return `$${(v / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(v) >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (Math.abs(v) >= 1_000) return `$${(v / 1_000).toFixed(1)}K`;
  return v.toFixed(1);
}

function EVTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-mono font-semibold text-primary">
        {formatValue(payload[0].value)}
      </p>
    </div>
  );
}

export function EVChart({ data, height = 350 }: EVChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground text-sm"
        style={{ height }}
      >
        No EV data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="evGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.15} />
            <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
          </linearGradient>
        </defs>
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
          tickFormatter={formatValue}
          width={60}
        />
        <Tooltip content={<EVTooltip />} />
        <Area
          type="monotone"
          dataKey="ev"
          stroke="var(--color-primary)"
          strokeWidth={2}
          fill="url(#evGradient)"
          dot={false}
          activeDot={{
            r: 4,
            fill: "var(--color-primary)",
            stroke: "var(--color-card)",
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
