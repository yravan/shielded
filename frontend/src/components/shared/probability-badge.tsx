import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ProbabilityBadgeProps {
  probability: number;
  className?: string;
}

function getColor(p: number) {
  if (p < 0.25) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (p < 0.5) return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
  if (p < 0.75) return "bg-orange-500/15 text-orange-400 border-orange-500/30";
  return "bg-red-500/15 text-red-400 border-red-500/30";
}

export function ProbabilityBadge({ probability, className }: ProbabilityBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("font-mono font-semibold text-sm", getColor(probability), className)}
    >
      {(probability * 100).toFixed(0)}%
    </Badge>
  );
}
