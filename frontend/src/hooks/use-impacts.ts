import { useQuery } from "@tanstack/react-query";
import type { EventImpactDaily } from "@/types";
import { apiFetch } from "@/lib/api-client";

/* eslint-disable @typescript-eslint/no-explicit-any */

async function fetchCompanyEventImpacts(companyId: string): Promise<EventImpactDaily[]> {
  const res = await apiFetch(`/api/companies/${companyId}/event-impacts`);
  if (!res.ok) throw new Error("Failed to fetch event impacts");
  const data = await res.json();
  return (data ?? []).map((raw: any) => ({
    eventId: raw.event_id,
    eventTitle: raw.event_title,
    eventCategory: raw.event_category,
    currentProbability: raw.current_probability,
    revenueImpactPerDay: raw.revenue_impact_per_day,
    opexImpactPerDay: raw.opex_impact_per_day,
    capexImpactPerDay: raw.capex_impact_per_day,
    totalImpactPerDay: raw.total_impact_per_day,
  }));
}

export function useCompanyEventImpacts(companyId: string | undefined) {
  return useQuery({
    queryKey: ["company-event-impacts", companyId],
    queryFn: () => fetchCompanyEventImpacts(companyId!),
    enabled: !!companyId,
  });
}

async function fetchEventImpactsForEvent(eventId: string): Promise<
  Array<EventImpactDaily & { companyId: string; companyName: string }>
> {
  // This uses the matched-companies endpoint + impact calculations
  // We'll fetch matched companies and their impacts
  const res = await apiFetch(`/api/events/${eventId}/matched-companies`);
  if (!res.ok) return [];
  const companies = await res.json();

  const impacts: Array<EventImpactDaily & { companyId: string; companyName: string }> = [];
  for (const company of companies ?? []) {
    try {
      const impactRes = await apiFetch(
        `/api/companies/${company.company_id}/event-impacts`
      );
      if (!impactRes.ok) continue;
      const companyImpacts = await impactRes.json();
      const match = (companyImpacts ?? []).find(
        (i: any) => i.event_id === eventId
      );
      if (match) {
        impacts.push({
          eventId: match.event_id,
          eventTitle: match.event_title,
          eventCategory: match.event_category,
          currentProbability: match.current_probability,
          revenueImpactPerDay: match.revenue_impact_per_day,
          opexImpactPerDay: match.opex_impact_per_day,
          capexImpactPerDay: match.capex_impact_per_day,
          totalImpactPerDay: match.total_impact_per_day,
          companyId: company.company_id,
          companyName: company.name,
        });
      }
    } catch {
      // skip failed companies
    }
  }
  return impacts;
}

export function useEventImpacts(eventId: string) {
  return useQuery({
    queryKey: ["event-impacts", eventId],
    queryFn: () => fetchEventImpactsForEvent(eventId),
    enabled: !!eventId,
  });
}
