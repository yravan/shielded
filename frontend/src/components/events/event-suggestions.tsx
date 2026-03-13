"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProbabilityBadge } from "@/components/shared/probability-badge";
import { useSuggestedEvents, useTrackEvent } from "@/hooks/use-events";
import { Plus, Check, Sparkles } from "lucide-react";
import type { SuggestedEvent } from "@/types";

function SuggestionCard({ suggestion }: { suggestion: SuggestedEvent }) {
  const trackMutation = useTrackEvent();

  return (
    <Card className="min-w-[280px] max-w-[320px] shrink-0 snap-start">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <Badge variant="outline" className="text-[10px] shrink-0">
            {suggestion.category}
          </Badge>
          <ProbabilityBadge probability={suggestion.currentProbability} />
        </div>

        <Link
          href={`/events/${suggestion.id}`}
          className="block hover:underline"
        >
          <h4 className="text-sm font-medium line-clamp-2 leading-snug">
            {suggestion.title}
          </h4>
        </Link>

        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="truncate">
            Matches: {suggestion.matchedCompanyName}
          </span>
          <span className="shrink-0 text-primary font-medium">
            {suggestion.relevanceScore}%
          </span>
        </div>

        <div className="flex flex-wrap gap-1">
          {suggestion.matchedThemes.slice(0, 3).map((theme) => (
            <Badge
              key={theme}
              variant="secondary"
              className="text-[10px] px-1 py-0"
            >
              {theme.replace(/_/g, " ")}
            </Badge>
          ))}
        </div>

        <Button
          size="sm"
          variant="default"
          className="w-full"
          disabled={trackMutation.isPending}
          onClick={() =>
            trackMutation.mutate({ eventId: suggestion.id, track: true })
          }
        >
          <Plus className="h-3.5 w-3.5 mr-1" />
          Track
        </Button>
      </CardContent>
    </Card>
  );
}

export function EventSuggestions() {
  const { data: suggestions, isLoading } = useSuggestedEvents();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold">Suggested Events</h3>
        </div>
        <div className="flex gap-4 overflow-hidden">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-[300px] shrink-0 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold">Suggested Events</h3>
        <span className="text-xs text-muted-foreground">
          Based on your company risk profiles
        </span>
      </div>
      <div className="flex gap-4 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin">
        {suggestions.map((s) => (
          <SuggestionCard key={s.id} suggestion={s} />
        ))}
      </div>
    </div>
  );
}
