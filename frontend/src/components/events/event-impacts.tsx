import { Badge } from "@/components/ui/badge";
import type { EventImpact } from "@/types";
import { cn } from "@/lib/utils";

interface EventImpactsProps {
  impacts: EventImpact[];
  compact?: boolean;
}

const severityColors = {
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function EventImpacts({ impacts, compact = false }: EventImpactsProps) {
  const displayImpacts = compact ? impacts.slice(0, 2) : impacts;

  return (
    <div className="space-y-1.5">
      {!compact && (
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Sector Impacts
        </p>
      )}
      {displayImpacts.map((impact, i) => (
        <div key={i} className="flex items-center justify-between gap-2">
          <span className={cn("text-sm", compact && "text-xs")}>{impact.sector}</span>
          <Badge variant="outline" className={cn("text-[10px]", severityColors[impact.severity])}>
            {impact.severity}
          </Badge>
        </div>
      ))}
      {compact && impacts.length > 2 && (
        <p className="text-xs text-muted-foreground">+{impacts.length - 2} more</p>
      )}
    </div>
  );
}
