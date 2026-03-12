import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/format";

interface CurrencyDisplayProps {
  value: number;
  compact?: boolean;
  className?: string;
}

export function CurrencyDisplay({ value, compact = true, className }: CurrencyDisplayProps) {
  return (
    <span className={cn("font-mono tabular-nums", className)}>
      {formatCurrency(value, compact)}
    </span>
  );
}
