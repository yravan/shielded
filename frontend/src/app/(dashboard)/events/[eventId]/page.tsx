"use client";

import { useState, useMemo, use } from "react";
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
import { EventImpactCards } from "@/components/events/event-impact-cards";
import { HedgeInstrumentsSection } from "@/components/events/hedge-instruments";
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
import { cn } from "@/lib/utils";
import { RiskScoreBadge } from "@/components/risk/risk-score-badge";
import { useMatchedCompanies } from "@/hooks/use-risk";
import type { TimeRange, GeopoliticalEvent, MatchedCompany } from "@/types";

const HOURS_MAP: Record<TimeRange, number> = {
  "1W": 168,
  "1M": 720,
  "YTD": Math.ceil((Date.now() - new Date(new Date().getFullYear(), 0, 1).getTime()) / 3_600_000),
  "1Y": 8760,
};

// ---------- Matched Companies section ----------

function MatchedCompaniesSection({ eventId }: { eventId: string }) {
  const { data: matched, isLoading } = useMatchedCompanies(eventId);

  if (isLoading) return <Skeleton className="h-24 w-full" />;
  if (!matched || matched.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Companies Affected ({matched.length})
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Companies matched by risk engine based on exposure profiles
        </p>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-border">
          {matched.map((company: MatchedCompany) => (
            <Link
              key={company.companyId}
              href={`/companies/${company.companyId}`}
              className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0 hover:bg-muted/50 -mx-2 px-2 rounded"
            >
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium">
                  {company.name}
                  {company.ticker && (
                    <span className="ml-1 text-muted-foreground font-mono text-xs">
                      ({company.ticker})
                    </span>
                  )}
                </span>
                <div className="flex gap-1 mt-0.5">
                  {company.matchedThemes.slice(0, 3).map((theme) => (
                    <Badge key={theme} variant="secondary" className="text-[10px] px-1 py-0">
                      {theme.replace(/_/g, " ")}
                    </Badge>
                  ))}
                </div>
              </div>
              <RiskScoreBadge score={company.relevanceScore} size="sm" showLabel={false} />
              <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------- Metadata bar (shared) ----------

function EventMetadata({ event }: { event: GeopoliticalEvent }) {
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
      <Badge variant="outline">{event.category}</Badge>
      {event.tags && event.tags.length > 0 && (
        event.tags.slice(0, 4).map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">
            {tag}
          </Badge>
        ))
      )}
      <span>{event.region}</span>
      <Separator orientation="vertical" className="h-4" />
      <span>Source: {event.source}</span>
      <Separator orientation="vertical" className="h-4" />
      <span>Resolves: {event.resolutionDate ? formatDate(event.resolutionDate) : "TBD"}</span>
      {event.volume != null && event.volume > 0 && (
        <>
          <Separator orientation="vertical" className="h-4" />
          <span>Vol: ${(event.volume / 1_000_000).toFixed(1)}M</span>
        </>
      )}
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

// ---------- Parent event detail view (unified layout) ----------

const LINE_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
  "#ec4899", "#06b6d4", "#f97316", "#6366f1", "#14b8a6",
];

function ParentEventDetail({ event }: { event: GeopoliticalEvent }) {
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null);
  const hours = HOURS_MAP[timeRange];
  const { data: childrenHistory, isLoading: historyLoading } = useParentEventHistory(event.id, hours);
  const trackMutation = useTrackEvent();
  const children = event.children ?? [];

  // Build market lines for multi-line chart (top 10)
  const marketLines = useMemo(() => {
    return children.slice(0, 10).map((child) => ({
      id: child.id,
      title: child.title,
      probability: child.currentProbability,
      history: childrenHistory?.[child.id]?.history ?? [],
    }));
  }, [children, childrenHistory]);

  const selectedChild = children.find((c) => c.id === selectedChildId);
  const selectedHistory = selectedChildId ? (childrenHistory?.[selectedChildId]?.history ?? []) : [];

  return (
    <div className="space-y-6">
      {/* Title + metadata */}
      <div>

        <div className="space-y-1">
          <h1 className="text-xl font-semibold">{event.title}</h1>
          <p className="text-sm text-muted-foreground">{event.description}</p>
        </div>
      </div>

      <EventMetadata event={event} />

      {/* Hero multi-line chart — full width, like binary event pages */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Probability History</CardTitle>
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

      {/* Markets list (left 1/4) + selected market chart (right 3/4) */}
      <div className="flex flex-col md:flex-row gap-4">
        <Card className="md:w-1/4 shrink-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Markets ({children.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-2">
            <div className="space-y-0.5">
              {children.map((child, index) => {
                const isSelected = selectedChildId === child.id;
                const color = LINE_COLORS[index % LINE_COLORS.length];
                return (
                  <div
                    key={child.id}
                    className={cn(
                      "flex items-center gap-2 px-2 py-2 rounded cursor-pointer transition-colors",
                      isSelected ? "bg-muted" : "hover:bg-muted/50"
                    )}
                    onClick={() => setSelectedChildId(isSelected ? null : child.id)}
                  >
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: index < 10 ? color : "var(--color-muted-foreground)" }}
                    />
                    <span className="text-xs flex-1 truncate">{child.title}</span>
                    <ProbabilityBadge probability={child.currentProbability} className="text-[11px] px-1.5 py-0" />
                    <Button
                      size="sm"
                      variant={child.isTracked ? "outline" : "ghost"}
                      className="shrink-0 h-6 w-6 p-0"
                      disabled={trackMutation.isPending}
                      onClick={(e) => {
                        e.stopPropagation();
                        trackMutation.mutate({
                          eventId: child.id,
                          track: !child.isTracked,
                        });
                      }}
                    >
                      {child.isTracked ? (
                        <Check className="h-3 w-3" />
                      ) : (
                        <Plus className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="flex-1 min-w-0">
          <CardContent className="pt-6">
            {selectedChild ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-medium truncate">{selectedChild.title}</h3>
                  <ProbabilityBadge probability={selectedChild.currentProbability} />
                </div>
                {historyLoading ? (
                  <Skeleton className="h-[300px] w-full" />
                ) : (
                  <ProbabilityChart data={selectedHistory} height={300} />
                )}
              </>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-sm text-muted-foreground">
                Select a market to view its individual chart
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <MatchedCompaniesSection eventId={event.id} />
    </div>
  );
}

// ---------- Child event detail view ----------

function ChildEventDetail({ event }: { event: GeopoliticalEvent }) {
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const hours = HOURS_MAP[timeRange];
  const { data: history } = useEventHistory(event.id, hours);
  const trackMutation = useTrackEvent();

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
          <ProbabilityChart data={history ?? []} height={350} />
        </CardContent>
      </Card>

      {(event.impacts.length > 0 || event.impliedFinancials.length > 0) && (
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
      )}

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

      <EventImpactCards eventId={event.id} />

      <HedgeInstrumentsSection eventId={event.id} />

      <MatchedCompaniesSection eventId={event.id} />

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
  const [timeRange, setTimeRange] = useState<TimeRange>("1M");
  const hours = HOURS_MAP[timeRange];
  const { data: history } = useEventHistory(event.id, hours);
  const trackMutation = useTrackEvent();

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
          <ProbabilityChart data={history ?? []} height={350} />
        </CardContent>
      </Card>

      {(event.impacts.length > 0 || event.impliedFinancials.length > 0) && (
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
      )}

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

      <EventImpactCards eventId={event.id} />

      <HedgeInstrumentsSection eventId={event.id} />

      <MatchedCompaniesSection eventId={event.id} />
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
