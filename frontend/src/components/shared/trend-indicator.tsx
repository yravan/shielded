import { ArrowUp, ArrowDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface TrendIndicatorProps {
  current: number;
  previous: number;
  className?: string;
}

export function TrendIndicator({ current, previous, className }: TrendIndicatorProps) {
  const change = current - previous;
  const changePercent = previous !== 0 ? (change / previous) * 100 : 0;

  if (Math.abs(changePercent) < 0.1) {
    return (
      <span className={cn("inline-flex items-center gap-0.5 text-xs text-muted-foreground", className)}>
        <Minus className="h-3 w-3" />
        <span>0.0%</span>
      </span>
    );
  }

  const isUp = change > 0;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 text-xs font-medium",
        isUp ? "text-red-400" : "text-emerald-400",
        className
      )}
    >
      {isUp ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
      <span>{Math.abs(changePercent).toFixed(1)}%</span>
    </span>
  );
}
