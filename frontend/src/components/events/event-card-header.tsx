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
  geopolitical: "bg-blue-500/20 text-blue-600 border-blue-500/40",
  trade: "bg-purple-500/20 text-purple-600 border-purple-500/40",
  regulatory: "bg-amber-500/20 text-amber-600 border-amber-500/40",
  climate: "bg-emerald-500/20 text-emerald-600 border-emerald-500/40",
  conflict: "bg-red-500/20 text-red-600 border-red-500/40",
  economic: "bg-cyan-500/20 text-cyan-600 border-cyan-500/40",
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
