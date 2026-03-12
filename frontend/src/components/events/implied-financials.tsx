import { cn } from "@/lib/utils";
import type { ImpliedFinancial } from "@/types";

interface ImpliedFinancialsProps {
  financials: ImpliedFinancial[];
  compact?: boolean;
}

export function ImpliedFinancials({ financials, compact = false }: ImpliedFinancialsProps) {
  const items = compact ? financials.slice(0, 3) : financials;

  return (
    <div className="space-y-1.5">
      {!compact && (
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Implied Moves
        </p>
      )}
      {items.map((f) => (
        <div key={f.ticker} className="flex items-center justify-between gap-2">
          <span className={cn("font-mono text-xs", compact ? "text-muted-foreground" : "")}>
            {f.ticker}
          </span>
          <span
            className={cn(
              "font-mono text-xs font-medium",
              f.impliedMovePercent < 0 ? "text-red-400" : "text-emerald-400"
            )}
          >
            {f.impliedMovePercent > 0 ? "+" : ""}
            {f.impliedMovePercent.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}
