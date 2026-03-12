import { Badge } from "@/components/ui/badge";
import { ProbabilityBadge } from "@/components/shared/probability-badge";
import { TrendIndicator } from "@/components/shared/trend-indicator";
import type { EventCategory } from "@/types";

interface EventCardHeaderProps {
  title: string;
  category: EventCategory;
  currentProbability: number;
  previousProbability: number;
}

const categoryColors: Record<EventCategory, string> = {
  geopolitical: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  trade: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  regulatory: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  climate: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  conflict: "bg-red-500/15 text-red-400 border-red-500/30",
  economic: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
};

export function EventCardHeader({
  title,
  category,
  currentProbability,
  previousProbability,
}: EventCardHeaderProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={categoryColors[category]}>
          {category}
        </Badge>
        <ProbabilityBadge probability={currentProbability} />
        <TrendIndicator current={currentProbability} previous={previousProbability} />
      </div>
      <h3 className="font-semibold leading-tight">{title}</h3>
    </div>
  );
}
