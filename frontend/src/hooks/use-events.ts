import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { GeopoliticalEvent, ProbabilityPoint } from "@/types";
import { apiFetch } from "@/lib/api-client";

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapApiEvent(raw: any): GeopoliticalEvent {
  return {
    id: raw.id,
    title: raw.title,
    description: raw.description,
    category: raw.category,
    currentProbability: raw.current_probability,
    previousProbability: raw.previous_probability ?? raw.current_probability,
    probabilityHistory: (raw.probability_history ?? []).map((p: any) => ({
      date: p.date ?? p.recorded_at,
      probability: p.probability,
    })),
    impacts: raw.impacts ?? [],
    impliedFinancials: raw.implied_financials ?? [],
    financialImpacts: raw.financial_impacts ?? [],
    resolutionDate: raw.resolution_date ?? null,
    source: raw.source,
    sourceUrl: raw.source_url,
    status: raw.status,
    region: raw.region,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    isTracked: raw.is_tracked ?? undefined,
    parentEventId: raw.parent_event_id ?? null,
    parentTitle: raw.parent_title ?? null,
    isParent: raw.is_parent ?? false,
    children: raw.children ? (raw.children as any[]).map(mapApiEvent) : undefined,
  };
}

// ---------- Tracked events (user's events) ----------

async function fetchEvents(): Promise<GeopoliticalEvent[]> {
  const res = await apiFetch("/api/events?page_size=100");
  if (!res.ok) throw new Error("Failed to fetch events");
  const data = await res.json();
  return (data.items ?? []).map(mapApiEvent);
}

async function fetchEvent(id: string): Promise<GeopoliticalEvent | undefined> {
  const res = await apiFetch(`/api/events/${id}`);
  if (!res.ok) throw new Error("Failed to fetch event");
  const raw = await res.json();
  return mapApiEvent(raw);
}

export function useEvents() {
  return useQuery({ queryKey: ["events"], queryFn: fetchEvents });
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ["events", id],
    queryFn: () => fetchEvent(id),
    enabled: !!id,
  });
}

// ---------- Explore events (all events) ----------

interface ExploreFilters {
  search?: string;
  category?: string;
  region?: string;
  sort?: string;
  page?: number;
  pageSize?: number;
}

async function fetchExploreEvents(
  filters: ExploreFilters
): Promise<{ items: GeopoliticalEvent[]; total: number; pages: number }> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.category && filters.category !== "all") params.set("category", filters.category);
  if (filters.region && filters.region !== "all") params.set("region", filters.region);
  if (filters.sort) params.set("sort", filters.sort);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 20));

  const res = await apiFetch(`/api/explore/events?${params}`);
  if (!res.ok) throw new Error("Failed to fetch events");
  const data = await res.json();
  return {
    items: (data.items ?? []).map(mapApiEvent),
    total: data.total ?? 0,
    pages: data.pages ?? 0,
  };
}

export function useExploreEvents(filters: ExploreFilters) {
  return useQuery({
    queryKey: ["explore-events", filters],
    queryFn: () => fetchExploreEvents(filters),
  });
}

// ---------- Track / Untrack ----------

export function useTrackEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ eventId, track }: { eventId: string; track: boolean }) => {
      const res = await apiFetch(`/api/events/${eventId}/track`, {
        method: track ? "POST" : "DELETE",
      });
      if (!res.ok) throw new Error("Failed to update tracking");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["explore-events"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

// ---------- Event history ----------

async function fetchEventHistory(id: string): Promise<ProbabilityPoint[]> {
  const res = await apiFetch(`/api/events/${id}/history`);
  if (!res.ok) throw new Error("Failed to fetch event history");
  const data = await res.json();
  return (data ?? []).map((p: any) => ({
    date: p.date ?? p.recorded_at,
    probability: p.probability,
  }));
}

export function useEventHistory(id: string) {
  return useQuery({
    queryKey: ["events", id, "history"],
    queryFn: () => fetchEventHistory(id),
    enabled: !!id,
  });
}

// ---------- Parent event children history ----------

export interface ChildHistory {
  title: string;
  history: ProbabilityPoint[];
}

async function fetchChildrenHistory(
  parentId: string
): Promise<Record<string, ChildHistory>> {
  const res = await apiFetch(`/api/events/${parentId}/children-history`);
  if (!res.ok) throw new Error("Failed to fetch children history");
  const data = await res.json();
  const children: Record<string, ChildHistory> = {};
  for (const [childId, child] of Object.entries(data.children ?? {})) {
    const c = child as any;
    children[childId] = {
      title: c.title,
      history: (c.history ?? []).map((p: any) => ({
        date: p.date ?? p.recorded_at,
        probability: p.probability,
      })),
    };
  }
  return children;
}

export function useParentEventHistory(parentId: string) {
  return useQuery({
    queryKey: ["events", parentId, "children-history"],
    queryFn: () => fetchChildrenHistory(parentId),
    enabled: !!parentId,
  });
}
