import { useQuery } from "@tanstack/react-query";
import {
  mockCompanies,
  getCompanyById,
  getCompanyExposures,
} from "@/lib/mock-data";
import { apiFetch } from "@/lib/api-client";
import type { Company, CompanyExposure } from "@/types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
/* eslint-disable @typescript-eslint/no-explicit-any */
function mapApiCompany(raw: any): Company {
  return {
    id: raw.id,
    name: raw.name,
    ticker: raw.ticker,
    sector: raw.sector,
    marketCap: 0,
    annualRevenue: raw.annual_revenue ?? 0,
    exposureCount: 0,
  };
}

function mapApiExposure(raw: any): CompanyExposure {
  return {
    id: raw.id,
    eventId: raw.event_id,
    eventTitle: raw.event_title ?? "",
    exposureType: raw.exposure_type,
    exposureDirection: raw.exposure_direction,
    sensitivity: raw.sensitivity,
    revenueAtRisk: raw.revenue_impact_pct ?? 0,
    revenueAtRiskPercent: raw.revenue_impact_pct ?? 0,
    hedgeRecommendation: "no_hedge",
    status: raw.status ?? "suggested",
    relevanceScore: raw.relevance_score ?? null,
    matchedThemes: raw.matched_themes ?? null,
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

async function fetchCompanies(): Promise<Company[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 300));
    return mockCompanies;
  }
  const res = await apiFetch("/api/companies");
  if (!res.ok) throw new Error("Failed to fetch companies");
  const data = await res.json();
  return data.map(mapApiCompany);
}

async function fetchCompany(id: string): Promise<Company | undefined> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 200));
    return getCompanyById(id);
  }
  const res = await apiFetch(`/api/companies/${id}`);
  if (!res.ok) throw new Error("Failed to fetch company");
  const raw = await res.json();
  return mapApiCompany(raw);
}

async function fetchCompanyExposures(
  companyId: string
): Promise<CompanyExposure[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 250));
    return getCompanyExposures(companyId);
  }
  const res = await apiFetch(`/api/companies/${companyId}/exposure`);
  if (!res.ok) throw new Error("Failed to fetch company exposures");
  const data = await res.json();
  return (data.exposures ?? []).map(mapApiExposure);
}

export function useCompanies() {
  return useQuery({ queryKey: ["companies"], queryFn: fetchCompanies });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: ["companies", id],
    queryFn: () => fetchCompany(id),
    enabled: !!id,
  });
}

export function useCompanyExposures(companyId: string) {
  return useQuery({
    queryKey: ["companies", companyId, "exposures"],
    queryFn: () => fetchCompanyExposures(companyId),
    enabled: !!companyId,
  });
}
