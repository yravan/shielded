"use client";

import { useState, use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/shared/page-header";
import { ProbabilityBadge } from "@/components/shared/probability-badge";
import { TrendIndicator } from "@/components/shared/trend-indicator";
import { ProbabilityChart } from "@/components/charts/probability-chart";
import { ChartTimeSelector } from "@/components/charts/chart-time-selector";
import { EventImpacts } from "@/components/events/event-impacts";
import { ImpliedFinancials } from "@/components/events/implied-financials";
import { useEvent } from "@/hooks/use-events";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/format";
import type { TimeRange, ProbabilityPoint } from "@/types";

function filterByTimeRange(data: ProbabilityPoint[], range: TimeRange): ProbabilityPoint[] {
  const now = new Date();
  let cutoff: Date;
  switch (range) {
    case "1W":
      cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case "1M":
      cutoff = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    case "YTD":
      cutoff = new Date(now.getFullYear(), 0, 1);
      break;
    case "1Y":
      cutoff = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
      break;
  }
  return data.filter((p) => new Date(p.date) >= cutoff);
}

export default function EventDetailPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = use(params);
  const { data: event, isLoading } = useEvent(eventId);
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[300px] w-full" />
      </div>
    );
  }

  if (!event) {
    return <p className="text-muted-foreground py-12 text-center">Event not found.</p>;
  }

  const filteredHistory = filterByTimeRange(event.probabilityHistory, timeRange);

  return (
    <div className="space-y-6">
      <PageHeader
        title={event.title}
        description={event.description}
        action={
          <div className="flex items-center gap-3">
            <ProbabilityBadge probability={event.currentProbability} />
            <TrendIndicator
              current={event.currentProbability}
              previous={event.previousProbability}
            />
          </div>
        }
      />

      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        <Badge variant="outline">{event.category}</Badge>
        <span>{event.region}</span>
        <Separator orientation="vertical" className="h-4" />
        <span>Source: {event.source}</span>
        <Separator orientation="vertical" className="h-4" />
        <span>Resolves: {formatDate(event.resolutionDate)}</span>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Probability History</CardTitle>
          <ChartTimeSelector value={timeRange} onChange={setTimeRange} />
        </CardHeader>
        <CardContent>
          <ProbabilityChart data={filteredHistory} height={350} />
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sector Impacts</CardTitle>
          </CardHeader>
          <CardContent>
            <EventImpacts impacts={event.impacts} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Implied Financial Moves</CardTitle>
          </CardHeader>
          <CardContent>
            <ImpliedFinancials financials={event.impliedFinancials} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
