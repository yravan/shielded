import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import type {
  CompanyRiskScore,
  MatchedCompany,
  PortfolioRiskSummary,
} from "@/types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapRiskScore(raw: any): CompanyRiskScore {
  return {
    companyId: raw.company_id,
    riskScore: raw.risk_score,
    avgScore: raw.avg_score,
    peakScore: raw.peak_score,
    eventCount: raw.event_count,
    matchedEvents: (raw.matched_events ?? []).map((e: any) => ({
      eventId: e.event_id,
      eventTitle: e.event_title,
      eventCategory: e.event_category,
      currentProbability: e.current_probability,
      relevanceScore: e.relevance_score,
      matchedThemes: e.matched_themes ?? [],
      explanation: e.explanation ?? "",
    })),
  };
}

function mapMatchedCompany(raw: any): MatchedCompany {
  return {
    companyId: raw.company_id,
    name: raw.name,
    ticker: raw.ticker,
    sector: raw.sector,
    relevanceScore: raw.relevance_score,
    matchedThemes: raw.matched_themes ?? [],
    explanation: raw.explanation ?? "",
  };
}

function mapPortfolioRisk(raw: any): PortfolioRiskSummary {
  return {
    totalCompanies: raw.total_companies,
    avgRiskScore: raw.avg_risk_score,
    highestRisk: raw.highest_risk ? mapMatchedCompany(raw.highest_risk) : null,
    topExposures: (raw.top_exposures ?? []).map((e: any) => ({
      eventId: e.event_id,
      eventTitle: e.event_title,
      eventCategory: e.event_category,
      currentProbability: e.current_probability,
      relevanceScore: e.relevance_score,
      matchedThemes: e.matched_themes ?? [],
      explanation: e.explanation ?? "",
    })),
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

export function useCompanyRisk(companyId: string) {
  return useQuery({
    queryKey: ["risk", "company", companyId],
    queryFn: async (): Promise<CompanyRiskScore> => {
      if (USE_MOCKS) {
        return {
          companyId,
          riskScore: 0,
          avgScore: 0,
          peakScore: 0,
          eventCount: 0,
          matchedEvents: [],
        };
      }
      const res = await apiFetch(`/api/companies/${companyId}/risk-score`);
      if (!res.ok) throw new Error("Failed to fetch risk score");
      return mapRiskScore(await res.json());
    },
    enabled: !!companyId,
  });
}

export function useMatchedCompanies(eventId: string) {
  return useQuery({
    queryKey: ["risk", "event", eventId, "matched-companies"],
    queryFn: async (): Promise<MatchedCompany[]> => {
      if (USE_MOCKS) return [];
      const res = await apiFetch(`/api/events/${eventId}/matched-companies`);
      if (!res.ok) throw new Error("Failed to fetch matched companies");
      const data = await res.json();
      return data.map(mapMatchedCompany);
    },
    enabled: !!eventId,
  });
}

export function usePortfolioRisk() {
  return useQuery({
    queryKey: ["risk", "portfolio"],
    queryFn: async (): Promise<PortfolioRiskSummary> => {
      if (USE_MOCKS) {
        return {
          totalCompanies: 0,
          avgRiskScore: 0,
          highestRisk: null,
          topExposures: [],
        };
      }
      const res = await apiFetch("/api/portfolio/risk-summary");
      if (!res.ok) throw new Error("Failed to fetch portfolio risk");
      return mapPortfolioRisk(await res.json());
    },
  });
}

export function useAcceptExposure() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (exposureId: string) => {
      const res = await apiFetch(`/api/exposures/${exposureId}/accept`, {
        method: "PUT",
      });
      if (!res.ok) throw new Error("Failed to accept exposure");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["risk"] });
    },
  });
}

export function useDismissExposure() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (exposureId: string) => {
      const res = await apiFetch(`/api/exposures/${exposureId}/dismiss`, {
        method: "PUT",
      });
      if (!res.ok) throw new Error("Failed to dismiss exposure");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["risk"] });
    },
  });
}
