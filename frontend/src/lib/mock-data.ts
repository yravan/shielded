/**
 * Mock data module — no longer used.
 * Events are now fetched live from the API.
 */
import type { GeopoliticalEvent, Company, CompanyExposure, HedgeComparison } from "@/types";

export const mockEvents: GeopoliticalEvent[] = [];
export const mockCompanies: Company[] = [];
export const mockHedgeComparisons: HedgeComparison[] = [];

export function getEventById(_id: string): GeopoliticalEvent | undefined {
  return undefined;
}
export function getCompanyById(_id: string): Company | undefined {
  return undefined;
}
export function getCompanyExposures(_companyId: string): CompanyExposure[] {
  return [];
}
export function getHedgeComparisonsForEvent(_eventId: string): HedgeComparison[] {
  return [];
}
