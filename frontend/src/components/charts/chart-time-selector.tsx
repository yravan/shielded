"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { TimeRange } from "@/types";

interface ChartTimeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
}

const ranges: TimeRange[] = ["1W", "1M", "YTD", "1Y"];

export function ChartTimeSelector({ value, onChange }: ChartTimeSelectorProps) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as TimeRange)}>
      <TabsList className="h-8">
        {ranges.map((r) => (
          <TabsTrigger key={r} value={r} className="text-xs px-3 h-6">
            {r}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
