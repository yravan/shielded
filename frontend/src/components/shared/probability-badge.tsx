import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ProbabilityBadgeProps {
  probability: number;
  className?: string;
}

function getColor(p: number) {
  if (p < 0.25) return "bg-emerald-500/20 text-emerald-600 border-emerald-500/40";
  if (p < 0.5) return "bg-yellow-500/20 text-yellow-600 border-yellow-500/40";
  if (p < 0.75) return "bg-orange-500/20 text-orange-600 border-orange-500/40";
  return "bg-red-500/20 text-red-600 border-red-500/40";
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
