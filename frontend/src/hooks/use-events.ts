import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { GeopoliticalEvent, ProbabilityPoint, SuggestedEvent } from "@/types";
import { apiFetch } from "@/lib/api-client";

const ZERO_UUID = "00000000-0000-0000-0000-000000000000";

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
    isQuantitative: raw.is_quantitative ?? false,
    expectedValue: raw.expected_value ?? null,
    children: raw.children ? (raw.children as any[]).map(mapApiEvent) : undefined,
    imageUrl: raw.image_url ?? null,
    tags: raw.tags ?? [],
    volume: raw.volume ?? null,
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
    enabled: !!id && id !== ZERO_UUID,
  });
}

// ---------- Suggested events ----------

async function fetchSuggestedEvents(): Promise<SuggestedEvent[]> {
  const res = await apiFetch("/api/events/suggestions");
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  const data = await res.json();
  return (data ?? []).map((raw: any) => ({
    id: raw.id,
    title: raw.title,
    description: raw.description,
    category: raw.category,
    region: raw.region,
    source: raw.source,
    sourceUrl: raw.source_url,
    currentProbability: raw.current_probability,
    resolutionDate: raw.resolution_date ?? null,
    status: raw.status,
    relevanceScore: raw.relevance_score,
    matchedCompanyName: raw.matched_company_name,
    matchedCompanyId: raw.matched_company_id,
    matchedThemes: raw.matched_themes ?? [],
    imageUrl: raw.image_url ?? null,
    tags: raw.tags ?? [],
  }));
}

export function useSuggestedEvents() {
  return useQuery({
    queryKey: ["suggested-events"],
    queryFn: fetchSuggestedEvents,
  });
}

// ---------- Explore events (all events) ----------

interface ExploreFilters {
  search?: string;
  category?: string;
  region?: string;
  source?: string;
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
  if (filters.source && filters.source !== "all") params.set("source", filters.source);
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
      queryClient.invalidateQueries({ queryKey: ["suggested-events"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

// ---------- Event history ----------

async function fetchEventHistory(id: string, hours?: number): Promise<ProbabilityPoint[]> {
  const params = hours ? `?hours=${hours}` : "";
  const res = await apiFetch(`/api/events/${id}/history${params}`);
  if (!res.ok) throw new Error("Failed to fetch event history");
  const data = await res.json();
  return (data ?? []).map((p: any) => ({
    date: p.date ?? p.recorded_at,
    probability: p.probability,
  }));
}

export function useEventHistory(id: string, hours?: number) {
  return useQuery({
    queryKey: ["events", id, "history", hours],
    queryFn: () => fetchEventHistory(id, hours),
    enabled: !!id && id !== ZERO_UUID,
  });
}

// ---------- Parent event children history ----------

export interface ChildHistory {
  title: string;
  history: ProbabilityPoint[];
}

async function fetchChildrenHistory(
  parentId: string,
  hours?: number,
): Promise<Record<string, ChildHistory>> {
  const params = hours ? `?hours=${hours}` : "";
  const res = await apiFetch(`/api/events/${parentId}/children-history${params}`);
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

export function useParentEventHistory(parentId: string, hours?: number) {
  return useQuery({
    queryKey: ["events", parentId, "children-history", hours],
    queryFn: () => fetchChildrenHistory(parentId, hours),
    enabled: !!parentId,
  });
}
