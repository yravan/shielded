export type EventCategory = "geopolitical" | "trade" | "regulatory" | "climate" | "conflict" | "economic";
export type EventStatus = "active" | "resolved" | "expired";
export type ExposureDirection = "negative" | "positive" | "mixed";
export type ExposureType = "revenue" | "supply_chain" | "regulatory" | "operational";
export type HedgeRecommendation = "prediction_market" | "traditional" | "blend" | "no_hedge";
export type TimeRange = "1W" | "1M" | "YTD" | "1Y";

export interface ProbabilityPoint {
  date: string;
  probability: number;
}

export interface EventImpact {
  sector: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
}

export interface ImpliedFinancial {
  ticker: string;
  name: string;
  currentPrice: number;
  impliedMove: number;
  impliedMovePercent: number;
}

export interface GeopoliticalEvent {
  id: string;
  title: string;
  description: string;
  category: EventCategory;
  currentProbability: number;
  previousProbability: number;
  probabilityHistory: ProbabilityPoint[];
  impacts: EventImpact[];
  impliedFinancials: ImpliedFinancial[];
  resolutionDate: string;
  source: string;
  sourceUrl: string;
  status: EventStatus;
  region: string;
  createdAt: string;
  updatedAt: string;
}

export interface Company {
  id: string;
  name: string;
  ticker: string;
  sector: string;
  marketCap: number;
  annualRevenue: number;
  exposureCount: number;
}

export interface CompanyExposure {
  id: string;
  eventId: string;
  eventTitle: string;
  exposureType: ExposureType;
  exposureDirection: ExposureDirection;
  sensitivity: number;
  revenueAtRisk: number;
  revenueAtRiskPercent: number;
  hedgeRecommendation: HedgeRecommendation;
}

export interface HedgeComparison {
  id: string;
  eventId: string;
  eventTitle: string;
  companyId: string;
  companyName: string;
  predictionMarket: {
    cost: number;
    payout: number;
    roi: number;
    instrument: string;
    platform: string;
  };
  traditional: {
    cost: number;
    payout: number;
    roi: number;
    instrument: string;
    provider: string;
  };
  recommendation: HedgeRecommendation;
  savingsPercent: number;
}
