import { useQuery } from "@tanstack/react-query";
import { mockHedgeComparisons } from "@/lib/mock-data";
import type { HedgeComparison } from "@/types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchHedgeComparisons(
  eventId?: string,
  companyId?: string
): Promise<HedgeComparison[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 300));
    let results = mockHedgeComparisons;
    if (eventId) {
      results = results.filter((h) => h.eventId === eventId);
    }
    if (companyId) {
      results = results.filter((h) => h.companyId === companyId);
    }
    return results;
  }

  const params = new URLSearchParams();
  if (eventId) params.set("event_id", eventId);
  if (companyId) params.set("company_id", companyId);

  const res = await fetch(
    `${API_URL}/api/hedge-comparisons?${params.toString()}`
  );
  if (!res.ok) throw new Error("Failed to fetch hedge comparisons");
  const data = await res.json();
  return data.items;
}

export function useHedgeComparisons(eventId?: string, companyId?: string) {
  return useQuery({
    queryKey: ["hedge-comparisons", eventId, companyId],
    queryFn: () => fetchHedgeComparisons(eventId, companyId),
  });
}
