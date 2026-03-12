"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ProbabilityPoint } from "@/types";

interface ProbabilityChartProps {
  data: ProbabilityPoint[];
  height?: number;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 shadow-lg">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-mono font-semibold text-primary">
        {(payload[0].value * 100).toFixed(1)}%
      </p>
    </div>
  );
}

export function ProbabilityChart({ data, height = 300 }: ProbabilityChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="probGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="oklch(0.65 0.19 250)" stopOpacity={0.3} />
            <stop offset="100%" stopColor="oklch(0.65 0.19 250)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: "oklch(0.60 0.02 250)" }}
          tickFormatter={(v) => {
            const d = new Date(v);
            return `${d.getMonth() + 1}/${d.getDate()}`;
          }}
          minTickGap={40}
        />
        <YAxis
          domain={[0, 1]}
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: "oklch(0.60 0.02 250)" }}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          width={45}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="probability"
          stroke="oklch(0.65 0.19 250)"
          strokeWidth={2}
          fill="url(#probGradient)"
          dot={false}
          activeDot={{ r: 4, fill: "oklch(0.65 0.19 250)", stroke: "oklch(0.16 0.02 250)", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
