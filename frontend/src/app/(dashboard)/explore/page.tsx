"use client";

import { useState, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ProbabilityBadge } from "@/components/shared/probability-badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useExploreEvents, useTrackEvent } from "@/hooks/use-events";
import { Search, Plus, Check, ChevronRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { GeopoliticalEvent } from "@/types";

const categories: Array<{ value: string; label: string }> = [
  { value: "all", label: "All" },
  { value: "geopolitical", label: "Geopolitical" },
  { value: "trade", label: "Trade" },
  { value: "regulatory", label: "Regulatory" },
  { value: "climate", label: "Climate" },
  { value: "conflict", label: "Conflict" },
  { value: "economic", label: "Economic" },
];

const regions: Array<{ value: string; label: string }> = [
  { value: "all", label: "All Regions" },
  { value: "Global", label: "Global" },
  { value: "North America", label: "North America" },
  { value: "Europe", label: "Europe" },
  { value: "Asia-Pacific", label: "Asia-Pacific" },
  { value: "Middle East", label: "Middle East" },
  { value: "Latin America", label: "Latin America" },
  { value: "Africa", label: "Africa" },
];

const sortOptions = [
  { value: "updated", label: "Recently Updated" },
  { value: "probability", label: "Highest Probability" },
  { value: "created", label: "Newest" },
];

const sources: Array<{ value: string; label: string }> = [
  { value: "all", label: "All Sources" },
  { value: "polymarket", label: "Polymarket" },
  { value: "kalshi", label: "Kalshi" },
];

function ExploreEventCard({
  event,
  onToggleTrack,
  isToggling,
}: {
  event: GeopoliticalEvent;
  onToggleTrack: (eventId: string, track: boolean) => void;
  isToggling: boolean;
}) {
  const tracked = event.isTracked ?? false;

  return (
    <Card className="flex flex-col">
      <CardContent className="flex flex-1 flex-col gap-2 pt-4">
        <div className="flex items-start justify-between gap-2">
          <Link href={`/events/${event.id}`} className="hover:underline">
            <h3 className="font-semibold text-sm leading-tight line-clamp-2">{event.title}</h3>
          </Link>
          <ProbabilityBadge probability={event.currentProbability} />
        </div>

        <p className="text-xs text-muted-foreground line-clamp-1">{event.description}</p>

        <div className="flex flex-wrap items-center gap-1.5 mt-auto">
          <Badge variant="outline" className="text-[11px]">
            {event.category}
          </Badge>
          <Badge variant="outline" className="text-[11px]">
            {event.region}
          </Badge>
          <span className="text-[10px] text-muted-foreground ml-auto">{event.source}</span>
        </div>

        <Button
          variant={tracked ? "outline" : "default"}
          size="sm"
          className="w-full"
          disabled={isToggling}
          onClick={() => onToggleTrack(event.id, !tracked)}
        >
          {tracked ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1.5" />
              Tracked
            </>
          ) : (
            <>
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Track
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

function stripParentPrefix(childTitle: string, parentTitle: string): string {
  // Find longest common prefix and show only the differentiating suffix
  const lower = childTitle.toLowerCase();
  const parentLower = parentTitle.toLowerCase();
  // Check word-level overlap
  const parentWords = parentLower.split(/\s+/);
  let matchLen = 0;
  for (let i = 0; i < parentWords.length; i++) {
    const prefix = parentWords.slice(0, i + 1).join(" ");
    if (lower.startsWith(prefix)) {
      matchLen = prefix.length;
    } else {
      break;
    }
  }
  if (matchLen > 10) {
    const suffix = childTitle.slice(matchLen).replace(/^[\s:—–-]+/, "").trim();
    if (suffix.length > 0) return suffix;
  }
  return childTitle;
}

function ChildMarketRow({ child, parentTitle }: { child: GeopoliticalEvent; parentTitle: string }) {
  const displayTitle = stripParentPrefix(child.title, parentTitle);

  return (
    <div className="flex items-center gap-1.5 py-1">
      <span className="text-xs truncate flex-1">{displayTitle}</span>
      <ProbabilityBadge probability={child.currentProbability} className="text-[11px] px-1.5 py-0" />
    </div>
  );
}

function ParentEventCard({
  event,
  onToggleTrack,
  isToggling,
}: {
  event: GeopoliticalEvent;
  onToggleTrack: (eventId: string, track: boolean) => void;
  isToggling: boolean;
}) {
  const children = event.children ?? [];
  const topChildren = children.slice(0, 3);
  const remainingCount = children.length - topChildren.length;
  const allTracked = children.length > 0 && children.every((c) => c.isTracked);

  const handleTrackAll = () => {
    for (const child of children) {
      if (!allTracked && !child.isTracked) {
        onToggleTrack(child.id, true);
      } else if (allTracked) {
        onToggleTrack(child.id, false);
      }
    }
  };

  return (
    <Card className="flex flex-col">
      <CardContent className="flex flex-1 flex-col gap-1.5 pt-4">
        <div className="flex items-start justify-between gap-2">
          <Link href={`/events/${event.id}`} className="hover:underline">
            <h3 className="font-semibold text-sm leading-tight line-clamp-2">{event.title}</h3>
          </Link>
          <Badge variant="outline" className="text-[11px] shrink-0">
            {children.length} markets
          </Badge>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline" className="text-[11px]">
            {event.category}
          </Badge>
          <Badge variant="outline" className="text-[11px]">
            {event.region}
          </Badge>
          <span className="text-[10px] text-muted-foreground ml-auto">{event.source}</span>
        </div>

        <div className="border-t border-border pt-1.5">
          {topChildren.map((child) => (
            <ChildMarketRow key={child.id} child={child} parentTitle={event.title} />
          ))}
        </div>

        <div className="flex items-center justify-between mt-auto pt-1">
          {remainingCount > 0 && (
            <span className="text-[10px] text-muted-foreground">
              +{remainingCount} more market{remainingCount > 1 ? "s" : ""}
            </span>
          )}
          <Link
            href={`/events/${event.id}`}
            className="text-xs text-primary hover:underline flex items-center gap-0.5 ml-auto"
          >
            View all <ChevronRight className="h-3 w-3" />
          </Link>
        </div>

        <Button
          variant={allTracked ? "outline" : "default"}
          size="sm"
          className="w-full"
          disabled={isToggling || children.length === 0}
          onClick={handleTrackAll}
        >
          {allTracked ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1.5" />
              Tracked
            </>
          ) : (
            <>
              <Plus className="h-3.5 w-3.5 mr-1.5" />
              Track All
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function ExplorePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const category = searchParams.get("category") || "all";
  const region = searchParams.get("region") || "all";
  const source = searchParams.get("source") || "all";
  const sort = searchParams.get("sort") || "updated";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const urlSearch = searchParams.get("q") || "";

  const [search, setSearch] = useState(urlSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(urlSearch);

  const updateParams = useCallback((updates: Record<string, string>) => {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (!value || value === "all" || (key === "sort" && value === "updated") || (key === "page" && value === "1")) {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    }
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  }, [searchParams, router, pathname]);

  const { data, isLoading } = useExploreEvents({
    search: debouncedSearch || undefined,
    category: category !== "all" ? category : undefined,
    region: region !== "all" ? region : undefined,
    source: source !== "all" ? source : undefined,
    sort,
    page,
    pageSize: 24,
  });

  const trackEvent = useTrackEvent();

  // Simple debounce on search
  const handleSearchChange = (value: string) => {
    setSearch(value);
    // Debounce 400ms
    const timeout = setTimeout(() => {
      setDebouncedSearch(value);
      updateParams({ q: value, page: "1" });
    }, 400);
    return () => clearTimeout(timeout);
  };

  const handleToggleTrack = (eventId: string, track: boolean) => {
    trackEvent.mutate({ eventId, track });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-1 border-b border-border overflow-x-auto pb-px">
        {categories.map((cat) => (
          <button
            key={cat.value}
            className={cn(
              "px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors",
              category === cat.value
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
            onClick={() => updateParams({ category: cat.value, page: "1" })}
          >
            {cat.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 shrink-0 pl-4">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search events..."
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-9 w-48 h-9"
            />
          </div>
          <Select value={region} onValueChange={(v) => updateParams({ region: v ?? "all", page: "1" })}>
            <SelectTrigger className="w-36 h-9">
              <SelectValue placeholder="Region" />
            </SelectTrigger>
            <SelectContent>
              {regions.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={source} onValueChange={(v) => updateParams({ source: v ?? "all", page: "1" })}>
            <SelectTrigger className="w-32 h-9">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              {sources.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sort} onValueChange={(v) => updateParams({ sort: v ?? "updated" })}>
            <SelectTrigger className="w-44 h-9">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              {sortOptions.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="pt-4 space-y-3">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                  <Skeleton className="h-8 w-full mt-2" />
                </CardContent>
              </Card>
            ))
          : data?.items.map((event) =>
              event.isParent ? (
                <ParentEventCard
                  key={event.id}
                  event={event}
                  onToggleTrack={handleToggleTrack}
                  isToggling={trackEvent.isPending}
                />
              ) : (
                <ExploreEventCard
                  key={event.id}
                  event={event}
                  onToggleTrack={handleToggleTrack}
                  isToggling={trackEvent.isPending}
                />
              )
            )}
      </div>

      {data?.items.length === 0 && !isLoading && (
        <p className="text-center text-muted-foreground py-12">
          No events match your search.
        </p>
      )}

      {data && data.pages > 1 && (
        <div className="flex justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => updateParams({ page: String(page - 1) })}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground self-center">
            Page {page} of {data.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.pages}
            onClick={() => updateParams({ page: String(page + 1) })}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
