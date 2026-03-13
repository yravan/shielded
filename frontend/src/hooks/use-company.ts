import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { UserCompany, CompanyLookup } from "@/types";
import { apiFetch } from "@/lib/api-client";

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapApiCompany(raw: any): UserCompany {
  return {
    id: raw.id,
    name: raw.name,
    ticker: raw.ticker ?? null,
    sector: raw.sector,
    annualRevenue: raw.annual_revenue ?? 0,
    operatingExpense: raw.operating_expense ?? 0,
    capitalExpense: raw.capital_expense ?? 0,
    createdAt: raw.created_at,
  };
}

// ── Multi-company hooks ────────────────────────────────────────────────

async function fetchMyCompanies(): Promise<UserCompany[]> {
  const res = await apiFetch("/api/my-companies");
  if (!res.ok) throw new Error("Failed to fetch companies");
  const data = await res.json();
  return data.map(mapApiCompany);
}

export function useMyCompanies() {
  return useQuery({
    queryKey: ["my-companies"],
    queryFn: fetchMyCompanies,
  });
}

interface SaveCompanyInput {
  name: string;
  ticker?: string | null;
  sector: string;
  annual_revenue: number;
  operating_expense: number;
  capital_expense: number;
}

export function useSaveCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SaveCompanyInput) => {
      const res = await apiFetch("/api/my-companies", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to save company");
      return mapApiCompany(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-companies"] });
      queryClient.invalidateQueries({ queryKey: ["my-company"] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: SaveCompanyInput }) => {
      const res = await apiFetch(`/api/my-companies/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Failed to update company");
      return mapApiCompany(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-companies"] });
      queryClient.invalidateQueries({ queryKey: ["my-company"] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useDeleteCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await apiFetch(`/api/my-companies/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete company");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-companies"] });
      queryClient.invalidateQueries({ queryKey: ["my-company"] });
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

// ── Backward-compatible single-company hooks ───────────────────────────

async function fetchMyCompany(): Promise<UserCompany | null> {
  const res = await apiFetch("/api/my-company");
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch company");
  return mapApiCompany(await res.json());
}

export function useMyCompany() {
  return useQuery({
    queryKey: ["my-company"],
    queryFn: fetchMyCompany,
  });
}

// ── Ticker lookup ──────────────────────────────────────────────────────

export function useCompanyLookup(ticker: string) {
  return useQuery({
    queryKey: ["company-lookup", ticker],
    queryFn: async (): Promise<CompanyLookup | null> => {
      if (!ticker || ticker.length < 1) return null;
      const res = await apiFetch(`/api/company-lookup/${ticker.toUpperCase()}`);
      if (res.status === 404 || res.status === 501) return null;
      if (!res.ok) throw new Error("Lookup failed");
      const raw = await res.json();
      return {
        name: raw.name,
        ticker: raw.ticker,
        sector: raw.sector,
        annualRevenue: raw.annual_revenue,
        operatingExpense: raw.operating_expense,
        capitalExpense: raw.capital_expense,
      };
    },
    enabled: !!ticker && ticker.length >= 1,
  });
}
