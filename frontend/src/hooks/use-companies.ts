import { useQuery } from "@tanstack/react-query";
import {
  mockCompanies,
  getCompanyById,
  getCompanyExposures,
} from "@/lib/mock-data";
import type { Company, CompanyExposure } from "@/types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchCompanies(): Promise<Company[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 300));
    return mockCompanies;
  }
  const res = await fetch(`${API_URL}/api/companies`);
  if (!res.ok) throw new Error("Failed to fetch companies");
  const data = await res.json();
  return data.items;
}

async function fetchCompany(id: string): Promise<Company | undefined> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 200));
    return getCompanyById(id);
  }
  const res = await fetch(`${API_URL}/api/companies/${id}`);
  if (!res.ok) throw new Error("Failed to fetch company");
  return res.json();
}

async function fetchCompanyExposures(
  companyId: string
): Promise<CompanyExposure[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 250));
    return getCompanyExposures(companyId);
  }
  const res = await fetch(`${API_URL}/api/companies/${companyId}/exposures`);
  if (!res.ok) throw new Error("Failed to fetch company exposures");
  const data = await res.json();
  return data.items;
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
