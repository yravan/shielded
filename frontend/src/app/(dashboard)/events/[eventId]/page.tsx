"use client";

import { useState, use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { ProbabilityBadge } from "@/components/shared/probability-badge";
import { TrendIndicator } from "@/components/shared/trend-indicator";
import { ProbabilityChart } from "@/components/charts/probability-chart";
import { MultiProbabilityChart } from "@/components/charts/multi-probability-chart";
import { ChartTimeSelector } from "@/components/charts/chart-time-selector";
import { EventImpacts } from "@/components/events/event-impacts";
import { ImpliedFinancials } from "@/components/events/implied-financials";
import { FinancialImpacts } from "@/components/events/financial-impacts";
import {
  useEvent,
  useEventHistory,
  useTrackEvent,
  useParentEventHistory,
} from "@/hooks/use-events";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/format";
import { ExternalLink, Check, Plus, ChevronRight } from "lucide-react";
import type { TimeRange, ProbabilityPoint, GeopoliticalEvent } from "@/types";

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

// ---------- Metadata bar (shared) ----------

function EventMetadata({ event }: { event: GeopoliticalEvent }) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
      <Badge variant="outline">{event.category}</Badge>
      <span>{event.region}</span>
      <Separator orientation="vertical" className="h-4" />
      <span>Source: {event.source}</span>
      <Separator orientation="vertical" className="h-4" />
      <span>Resolves: {event.resolutionDate ? formatDate(event.resolutionDate) : "TBD"}</span>
      {event.sourceUrl && (
        <>
          <Separator orientation="vertical" className="h-4" />
          <a
            href={event.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            View Source <ExternalLink className="h-3 w-3" />
          </a>
        </>
      )}
    </div>
  );
}

// ---------- Parent event detail view ----------

function ParentEventDetail({ event }: { event: GeopoliticalEvent }) {
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const { data: childrenHistory, isLoading: historyLoading } = useParentEventHistory(event.id);
  const trackMutation = useTrackEvent();
  const children = event.children ?? [];

  // Build market lines for the multi-chart
  const marketLines = children.slice(0, 5).map((child) => ({
    id: child.id,
    title: child.title,
    probability: child.currentProbability,
    history: childrenHistory?.[child.id]?.history
      ? filterByTimeRange(childrenHistory[child.id].history, timeRange)
      : [],
  }));

  return (
    <div className="space-y-8">
      <div>
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">{event.title}</h1>
          <p className="text-sm text-muted-foreground">{event.description}</p>
        </div>
      </div>

      <EventMetadata event={event} />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Market Probabilities</CardTitle>
          <ChartTimeSelector value={timeRange} onChange={setTimeRange} />
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Skeleton className="h-[350px] w-full" />
          ) : (
            <MultiProbabilityChart markets={marketLines} height={350} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Markets ({children.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-border">
            {children.map((child) => (
              <div
                key={child.id}
                className="flex items-center gap-3 py-3 first:pt-0 last:pb-0"
              >
                <Link
                  href={`/events/${child.id}`}
                  className="text-sm font-medium hover:underline flex-1 truncate"
                >
                  {child.title}
                </Link>
                <ProbabilityBadge probability={child.currentProbability} />
                <Button
                  size="sm"
                  variant={child.isTracked ? "outline" : "default"}
                  className="shrink-0"
                  disabled={trackMutation.isPending}
                  onClick={() =>
                    trackMutation.mutate({
                      eventId: child.id,
                      track: !child.isTracked,
                    })
                  }
                >
                  {child.isTracked ? (
                    <>
                      <Check className="h-3.5 w-3.5 mr-1" />
                      Tracked
                    </>
                  ) : (
                    <>
                      <Plus className="h-3.5 w-3.5 mr-1" />
                      Track
                    </>
                  )}
                </Button>
                <Link href={`/events/${child.id}`}>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ---------- Child event detail view ----------

function ChildEventDetail({ event }: { event: GeopoliticalEvent }) {
  const { data: history } = useEventHistory(event.id);
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const trackMutation = useTrackEvent();

  const filteredHistory = filterByTimeRange(history ?? [], timeRange);
  // Siblings are stored in event.children when viewing a child
  const siblings = event.children ?? [];

  return (
    <div className="space-y-8">
      <div>
        {event.parentTitle && event.parentEventId && (
          <Link
            href={`/events/${event.parentEventId}`}
            className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2"
          >
            Part of: {event.parentTitle} <ChevronRight className="h-3 w-3" />
          </Link>
        )}
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold">{event.title}</h1>
            <p className="text-sm text-muted-foreground">{event.description}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <ProbabilityBadge probability={event.currentProbability} />
            <TrendIndicator
              current={event.currentProbability}
              previous={event.previousProbability}
            />
            <Button
              size="sm"
              variant={event.isTracked ? "secondary" : "default"}
              disabled={trackMutation.isPending}
              onClick={() =>
                trackMutation.mutate({
                  eventId: event.id,
                  track: !event.isTracked,
                })
              }
            >
              {event.isTracked ? (
                <>
                  <Check className="h-4 w-4 mr-1" />
                  Tracked
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-1" />
                  Track
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <EventMetadata event={event} />

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

      {event.financialImpacts && event.financialImpacts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Company Financial Impact Analysis</CardTitle>
            <p className="text-xs text-muted-foreground">
              Estimated impact on company financials if this event occurs
            </p>
          </CardHeader>
          <CardContent>
            <FinancialImpacts impacts={event.financialImpacts} />
          </CardContent>
        </Card>
      )}

      {siblings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Related Markets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {siblings.map((sibling) => (
                <Link
                  key={sibling.id}
                  href={`/events/${sibling.id}`}
                  className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0 hover:bg-muted/50 -mx-2 px-2 rounded"
                >
                  <span className="text-sm truncate flex-1">{sibling.title}</span>
                  <ProbabilityBadge probability={sibling.currentProbability} />
                  <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------- Flat event detail view (existing behavior) ----------

function FlatEventDetail({ event }: { event: GeopoliticalEvent }) {
  const { data: history } = useEventHistory(event.id);
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const trackMutation = useTrackEvent();

  const filteredHistory = filterByTimeRange(history ?? [], timeRange);

  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold">{event.title}</h1>
            <p className="text-sm text-muted-foreground">{event.description}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <ProbabilityBadge probability={event.currentProbability} />
            <TrendIndicator
              current={event.currentProbability}
              previous={event.previousProbability}
            />
            <Button
              size="sm"
              variant={event.isTracked ? "secondary" : "default"}
              disabled={trackMutation.isPending}
              onClick={() =>
                trackMutation.mutate({
                  eventId: event.id,
                  track: !event.isTracked,
                })
              }
            >
              {event.isTracked ? (
                <>
                  <Check className="h-4 w-4 mr-1" />
                  Tracked
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-1" />
                  Track
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <EventMetadata event={event} />

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

      {event.financialImpacts && event.financialImpacts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Company Financial Impact Analysis</CardTitle>
            <p className="text-xs text-muted-foreground">
              Estimated impact on company financials if this event occurs
            </p>
          </CardHeader>
          <CardContent>
            <FinancialImpacts impacts={event.financialImpacts} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ---------- Page component ----------

export default function EventDetailPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = use(params);
  const { data: event, isLoading } = useEvent(eventId);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[300px] w-full" />
      </div>
    );
  }

  if (!event) {
    return <p className="text-muted-foreground py-12 text-center">Event not found.</p>;
  }

  if (event.isParent) {
    return <ParentEventDetail event={event} />;
  }

  if (event.parentEventId) {
    return <ChildEventDetail event={event} />;
  }

  return <FlatEventDetail event={event} />;
}
