"use client";

import { AreaChart, Area, ResponsiveContainer } from "recharts";
import type { ProbabilityPoint } from "@/types";

interface MiniSparklineProps {
  data: ProbabilityPoint[];
  width?: number;
  height?: number;
}

export function MiniSparkline({ data, width = 80, height = 30 }: MiniSparklineProps) {
  const last20 = data.slice(-20);

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={last20} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="oklch(0.65 0.19 250)" stopOpacity={0.3} />
              <stop offset="100%" stopColor="oklch(0.65 0.19 250)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="probability"
            stroke="oklch(0.65 0.19 250)"
            strokeWidth={1.5}
            fill="url(#sparkGradient)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
