"use client";

import { AreaChart, Area, ResponsiveContainer } from "recharts";
import type { ProbabilityPoint } from "@/types";

interface MiniSparklineProps {
  data: ProbabilityPoint[];
  width?: number;
  height?: number;
  loading?: boolean;
}

export function MiniSparkline({ data, width = 80, height = 30, loading }: MiniSparklineProps) {
  if (loading) {
    return (
      <div
        style={{ width, height }}
        className="rounded bg-muted animate-pulse"
      />
    );
  }

  if (!data || data.length === 0) {
    return (
      <div
        style={{ width, height }}
        className="rounded bg-muted/50 flex items-center justify-center"
      >
        <span className="text-[9px] text-muted-foreground">No data</span>
      </div>
    );
  }

  const last20 = data.slice(-20);

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={last20} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.15} />
              <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="probability"
            stroke="var(--color-primary)"
            strokeWidth={1.5}
            fill="url(#sparkGradient)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
