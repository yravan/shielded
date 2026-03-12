import type {
  GeopoliticalEvent,
  Company,
  CompanyExposure,
  HedgeComparison,
  ProbabilityPoint,
} from "@/types";
import { format, subDays } from "date-fns";

function generateProbabilityHistory(
  baseProb: number,
  volatility: number,
  days: number = 90
): ProbabilityPoint[] {
  const points: ProbabilityPoint[] = [];
  let current = baseProb;
  const today = new Date();

  for (let i = days; i >= 0; i--) {
    const date = subDays(today, i);
    points.push({
      date: format(date, "yyyy-MM-dd"),
      probability: Math.round(current * 1000) / 1000,
    });
    current += (Math.random() - 0.5) * volatility;
    current = Math.max(0.01, Math.min(0.99, current));
  }

  // Ensure the last point matches baseProb closely
  points[points.length - 1].probability = baseProb;

  return points;
}

// ─── Events ──────────────────────────────────────────────────────────────────

export const mockEvents: GeopoliticalEvent[] = [
  {
    id: "evt-001",
    title: "Iran Strait of Hormuz Disruption",
    description:
      "Escalating tensions between Iran and Western nations raise the risk of a partial or full blockade of the Strait of Hormuz, through which approximately 21% of global petroleum passes daily. Recent IRGC naval exercises and rhetoric around retaliatory measures have elevated shipping insurance premiums.",
    category: "conflict",
    currentProbability: 0.3,
    previousProbability: 0.26,
    probabilityHistory: generateProbabilityHistory(0.3, 0.04),
    impacts: [
      {
        sector: "Energy",
        severity: "critical",
        description:
          "Oil prices could spike 40-80% if strait is blocked; LNG shipments severely disrupted",
      },
      {
        sector: "Shipping",
        severity: "high",
        description:
          "Rerouting around Cape of Good Hope adds 10-15 days transit time and significant fuel costs",
      },
      {
        sector: "Chemicals",
        severity: "high",
        description:
          "Petrochemical feedstock supply chains disrupted; Middle East exports account for 30% of global ethylene",
      },
    ],
    impliedFinancials: [
      {
        ticker: "XOM",
        name: "ExxonMobil",
        currentPrice: 118.45,
        impliedMove: 14.2,
        impliedMovePercent: 12.0,
      },
      {
        ticker: "MAERSK-B",
        name: "Maersk",
        currentPrice: 14200,
        impliedMove: -2130,
        impliedMovePercent: -15.0,
      },
      {
        ticker: "BAS",
        name: "BASF",
        currentPrice: 48.9,
        impliedMove: -5.87,
        impliedMovePercent: -12.0,
      },
    ],
    resolutionDate: "2026-09-30",
    source: "Polymarket",
    sourceUrl: "https://polymarket.com/event/hormuz-disruption",
    status: "active",
    region: "Middle East",
    createdAt: "2025-11-15T08:00:00Z",
    updatedAt: "2026-03-11T14:30:00Z",
  },
  {
    id: "evt-002",
    title: "EU Carbon Border Tax Expansion",
    description:
      "The European Commission is advancing plans to expand CBAM (Carbon Border Adjustment Mechanism) to cover additional product categories including chemicals, plastics, and certain manufactured goods by 2027. Current coverage of cement, steel, aluminum, fertilizers, electricity, and hydrogen would broaden significantly.",
    category: "regulatory",
    currentProbability: 0.72,
    previousProbability: 0.68,
    probabilityHistory: generateProbabilityHistory(0.72, 0.03),
    impacts: [
      {
        sector: "Chemicals",
        severity: "high",
        description:
          "European chemical importers face 8-15% cost increases on non-EU sourced products",
      },
      {
        sector: "Manufacturing",
        severity: "medium",
        description:
          "Supply chain restructuring needed to comply with carbon reporting requirements",
      },
      {
        sector: "Technology",
        severity: "low",
        description:
          "Semiconductor manufacturing may face indirect cost increases through chemical inputs",
      },
    ],
    impliedFinancials: [
      {
        ticker: "BAS",
        name: "BASF",
        currentPrice: 48.9,
        impliedMove: -3.42,
        impliedMovePercent: -7.0,
      },
      {
        ticker: "LIN",
        name: "Linde",
        currentPrice: 472.3,
        impliedMove: 23.6,
        impliedMovePercent: 5.0,
      },
    ],
    resolutionDate: "2026-12-31",
    source: "Metaculus",
    sourceUrl: "https://metaculus.com/questions/eu-cbam-expansion",
    status: "active",
    region: "Europe",
    createdAt: "2025-09-01T10:00:00Z",
    updatedAt: "2026-03-10T09:15:00Z",
  },
  {
    id: "evt-003",
    title: "China-Taiwan Military Escalation",
    description:
      "PLA military drills in the Taiwan Strait have intensified following diplomatic incidents. While a full invasion remains unlikely in the near term, a naval blockade or escalatory incident could severely disrupt the global semiconductor supply chain. TSMC produces over 60% of the world's advanced chips.",
    category: "conflict",
    currentProbability: 0.08,
    previousProbability: 0.06,
    probabilityHistory: generateProbabilityHistory(0.08, 0.015),
    impacts: [
      {
        sector: "Semiconductors",
        severity: "critical",
        description:
          "Global chip supply would face catastrophic disruption; TSMC produces 90% of sub-7nm chips",
      },
      {
        sector: "Technology",
        severity: "critical",
        description:
          "Apple, NVIDIA, AMD, and Qualcomm face months of production halts",
      },
      {
        sector: "Automotive",
        severity: "high",
        description:
          "Auto production would face renewed chip shortages worse than 2021-2022",
      },
      {
        sector: "Defense",
        severity: "medium",
        description:
          "Defense contractors would see increased orders but face own supply chain challenges",
      },
    ],
    impliedFinancials: [
      {
        ticker: "TSM",
        name: "TSMC",
        currentPrice: 178.5,
        impliedMove: -53.55,
        impliedMovePercent: -30.0,
      },
      {
        ticker: "AAPL",
        name: "Apple",
        currentPrice: 232.8,
        impliedMove: -34.92,
        impliedMovePercent: -15.0,
      },
      {
        ticker: "NVDA",
        name: "NVIDIA",
        currentPrice: 142.6,
        impliedMove: -35.65,
        impliedMovePercent: -25.0,
      },
    ],
    resolutionDate: "2027-06-30",
    source: "Metaculus",
    sourceUrl: "https://metaculus.com/questions/china-taiwan-escalation",
    status: "active",
    region: "Asia Pacific",
    createdAt: "2025-06-01T12:00:00Z",
    updatedAt: "2026-03-12T07:45:00Z",
  },
  {
    id: "evt-004",
    title: "OPEC+ Production Cut Extension",
    description:
      "Saudi Arabia is pushing OPEC+ members to extend voluntary production cuts of 2.2 million barrels/day through Q4 2026. Russia and UAE compliance remains questionable. Extension would keep Brent above $85/barrel; failure could push prices toward $65.",
    category: "economic",
    currentProbability: 0.45,
    previousProbability: 0.52,
    probabilityHistory: generateProbabilityHistory(0.45, 0.05),
    impacts: [
      {
        sector: "Energy",
        severity: "high",
        description:
          "Oil majors benefit from sustained high prices; upstream capex plans remain robust",
      },
      {
        sector: "Shipping",
        severity: "medium",
        description:
          "Higher bunker fuel costs compress shipping margins",
      },
      {
        sector: "Airlines",
        severity: "high",
        description:
          "Jet fuel costs represent 25-30% of airline operating expenses",
      },
    ],
    impliedFinancials: [
      {
        ticker: "XOM",
        name: "ExxonMobil",
        currentPrice: 118.45,
        impliedMove: 8.29,
        impliedMovePercent: 7.0,
      },
      {
        ticker: "MAERSK-B",
        name: "Maersk",
        currentPrice: 14200,
        impliedMove: -568,
        impliedMovePercent: -4.0,
      },
    ],
    resolutionDate: "2026-06-30",
    source: "Kalshi",
    sourceUrl: "https://kalshi.com/markets/opec-cut-extension",
    status: "active",
    region: "Middle East",
    createdAt: "2025-12-01T08:00:00Z",
    updatedAt: "2026-03-11T16:00:00Z",
  },
  {
    id: "evt-005",
    title: "US TikTok Ban Implementation",
    description:
      "Following the Supreme Court upholding the divest-or-ban law, ByteDance faces a final deadline to divest TikTok's US operations. A consortium including Oracle and several PE firms is in advanced talks, but CCP approval remains a significant hurdle. Full ban would affect 170M US users.",
    category: "regulatory",
    currentProbability: 0.61,
    previousProbability: 0.58,
    probabilityHistory: generateProbabilityHistory(0.61, 0.04),
    impacts: [
      {
        sector: "Technology",
        severity: "high",
        description:
          "Meta and YouTube/Google would absorb significant ad revenue and user engagement",
      },
      {
        sector: "Advertising",
        severity: "medium",
        description:
          "Digital ad market restructuring; $12B+ in US TikTok ad revenue to redistribute",
      },
    ],
    impliedFinancials: [
      {
        ticker: "AAPL",
        name: "Apple",
        currentPrice: 232.8,
        impliedMove: -4.66,
        impliedMovePercent: -2.0,
      },
      {
        ticker: "META",
        name: "Meta Platforms",
        currentPrice: 612.4,
        impliedMove: 42.87,
        impliedMovePercent: 7.0,
      },
    ],
    resolutionDate: "2026-07-15",
    source: "Polymarket",
    sourceUrl: "https://polymarket.com/event/tiktok-ban",
    status: "active",
    region: "North America",
    createdAt: "2025-01-20T10:00:00Z",
    updatedAt: "2026-03-10T11:30:00Z",
  },
  {
    id: "evt-006",
    title: "Russia-Ukraine Ceasefire Agreement",
    description:
      "Diplomatic channels have reopened following backchannel negotiations involving Turkey and Gulf states. A ceasefire framework is being discussed involving partial territorial concessions, security guarantees, and phased sanctions relief. European energy markets and defense stocks would be significantly impacted.",
    category: "conflict",
    currentProbability: 0.25,
    previousProbability: 0.19,
    probabilityHistory: generateProbabilityHistory(0.25, 0.04),
    impacts: [
      {
        sector: "Energy",
        severity: "high",
        description:
          "European natural gas prices could drop 20-30% on restored pipeline flows",
      },
      {
        sector: "Defense",
        severity: "medium",
        description:
          "European defense contractors may see order slowdowns; US defense less affected",
      },
      {
        sector: "Agriculture",
        severity: "medium",
        description:
          "Black Sea grain corridor fully reopens; wheat and corn prices normalize",
      },
    ],
    impliedFinancials: [
      {
        ticker: "BAS",
        name: "BASF",
        currentPrice: 48.9,
        impliedMove: 4.89,
        impliedMovePercent: 10.0,
      },
      {
        ticker: "XOM",
        name: "ExxonMobil",
        currentPrice: 118.45,
        impliedMove: -7.11,
        impliedMovePercent: -6.0,
      },
    ],
    resolutionDate: "2026-12-31",
    source: "Metaculus",
    sourceUrl: "https://metaculus.com/questions/ukraine-ceasefire",
    status: "active",
    region: "Europe",
    createdAt: "2025-08-10T14:00:00Z",
    updatedAt: "2026-03-12T08:00:00Z",
  },
  {
    id: "evt-007",
    title: "US Semiconductor Export Controls Expansion",
    description:
      "The Commerce Department is finalizing new rules to further restrict semiconductor equipment and AI chip exports to China. Expanded entity list additions and closing of third-country transshipment loopholes would affect equipment makers and chip designers with significant China revenue exposure.",
    category: "trade",
    currentProbability: 0.55,
    previousProbability: 0.50,
    probabilityHistory: generateProbabilityHistory(0.55, 0.04),
    impacts: [
      {
        sector: "Semiconductors",
        severity: "high",
        description:
          "Equipment makers like ASML, Applied Materials, Lam Research lose 10-25% of China revenue",
      },
      {
        sector: "Technology",
        severity: "medium",
        description:
          "NVIDIA and AMD face further restrictions on AI accelerator sales to China",
      },
      {
        sector: "Manufacturing",
        severity: "medium",
        description:
          "Accelerated reshoring of chip fabrication; increased demand for domestic capacity",
      },
    ],
    impliedFinancials: [
      {
        ticker: "TSM",
        name: "TSMC",
        currentPrice: 178.5,
        impliedMove: -10.71,
        impliedMovePercent: -6.0,
      },
      {
        ticker: "AAPL",
        name: "Apple",
        currentPrice: 232.8,
        impliedMove: -9.31,
        impliedMovePercent: -4.0,
      },
      {
        ticker: "ASML",
        name: "ASML Holding",
        currentPrice: 742.0,
        impliedMove: -81.62,
        impliedMovePercent: -11.0,
      },
    ],
    resolutionDate: "2026-09-30",
    source: "Kalshi",
    sourceUrl: "https://kalshi.com/markets/chip-export-controls",
    status: "active",
    region: "Global",
    createdAt: "2025-10-15T09:00:00Z",
    updatedAt: "2026-03-11T13:00:00Z",
  },
  {
    id: "evt-008",
    title: "Red Sea Shipping Disruption Escalation",
    description:
      "Houthi attacks on commercial shipping in the Red Sea and Bab el-Mandeb strait continue despite US-led naval operations. Major container lines have rerouted via the Cape of Good Hope. Escalation scenarios include expanded target zones and mine-laying that could close the strait entirely.",
    category: "geopolitical",
    currentProbability: 0.65,
    previousProbability: 0.60,
    probabilityHistory: generateProbabilityHistory(0.65, 0.05),
    impacts: [
      {
        sector: "Shipping",
        severity: "critical",
        description:
          "Container rates on Asia-Europe routes up 300-400%; transit times increased by 10-14 days",
      },
      {
        sector: "Retail",
        severity: "high",
        description:
          "Supply chain delays impact inventory planning; holiday season goods require earlier ordering",
      },
      {
        sector: "Energy",
        severity: "medium",
        description:
          "LNG tanker rerouting increases delivered gas costs to Europe by 15-20%",
      },
      {
        sector: "Insurance",
        severity: "high",
        description:
          "War risk insurance premiums for Red Sea transit at 0.5-1.0% of cargo value",
      },
    ],
    impliedFinancials: [
      {
        ticker: "MAERSK-B",
        name: "Maersk",
        currentPrice: 14200,
        impliedMove: 2840,
        impliedMovePercent: 20.0,
      },
      {
        ticker: "XOM",
        name: "ExxonMobil",
        currentPrice: 118.45,
        impliedMove: 4.74,
        impliedMovePercent: 4.0,
      },
    ],
    resolutionDate: "2026-12-31",
    source: "Polymarket",
    sourceUrl: "https://polymarket.com/event/red-sea-shipping",
    status: "active",
    region: "Middle East",
    createdAt: "2024-12-01T08:00:00Z",
    updatedAt: "2026-03-12T10:00:00Z",
  },
];

// ─── Companies ───────────────────────────────────────────────────────────────

export const mockCompanies: Company[] = [
  {
    id: "comp-001",
    name: "ExxonMobil",
    ticker: "XOM",
    sector: "Energy",
    marketCap: 498_000_000_000,
    annualRevenue: 344_600_000_000,
    exposureCount: 4,
  },
  {
    id: "comp-002",
    name: "Maersk",
    ticker: "MAERSK-B",
    sector: "Shipping",
    marketCap: 28_400_000_000,
    annualRevenue: 51_000_000_000,
    exposureCount: 3,
  },
  {
    id: "comp-003",
    name: "TSMC",
    ticker: "TSM",
    sector: "Semiconductors",
    marketCap: 920_000_000_000,
    annualRevenue: 87_100_000_000,
    exposureCount: 3,
  },
  {
    id: "comp-004",
    name: "BASF",
    ticker: "BAS",
    sector: "Chemicals",
    marketCap: 43_500_000_000,
    annualRevenue: 68_900_000_000,
    exposureCount: 3,
  },
  {
    id: "comp-005",
    name: "Apple",
    ticker: "AAPL",
    sector: "Technology",
    marketCap: 3_560_000_000_000,
    annualRevenue: 383_300_000_000,
    exposureCount: 3,
  },
];

// ─── Company Exposures ───────────────────────────────────────────────────────

const mockExposures: Record<string, CompanyExposure[]> = {
  "comp-001": [
    {
      id: "exp-001",
      eventId: "evt-001",
      eventTitle: "Iran Strait of Hormuz Disruption",
      exposureType: "revenue",
      exposureDirection: "positive",
      sensitivity: 0.85,
      revenueAtRisk: 41_350_000_000,
      revenueAtRiskPercent: 12.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-002",
      eventId: "evt-004",
      eventTitle: "OPEC+ Production Cut Extension",
      exposureType: "revenue",
      exposureDirection: "positive",
      sensitivity: 0.72,
      revenueAtRisk: 24_122_000_000,
      revenueAtRiskPercent: 7.0,
      hedgeRecommendation: "blend",
    },
    {
      id: "exp-003",
      eventId: "evt-006",
      eventTitle: "Russia-Ukraine Ceasefire Agreement",
      exposureType: "revenue",
      exposureDirection: "negative",
      sensitivity: 0.45,
      revenueAtRisk: 17_230_000_000,
      revenueAtRiskPercent: 5.0,
      hedgeRecommendation: "traditional",
    },
    {
      id: "exp-004",
      eventId: "evt-008",
      eventTitle: "Red Sea Shipping Disruption Escalation",
      exposureType: "operational",
      exposureDirection: "mixed",
      sensitivity: 0.35,
      revenueAtRisk: 6_892_000_000,
      revenueAtRiskPercent: 2.0,
      hedgeRecommendation: "no_hedge",
    },
  ],
  "comp-002": [
    {
      id: "exp-005",
      eventId: "evt-001",
      eventTitle: "Iran Strait of Hormuz Disruption",
      exposureType: "operational",
      exposureDirection: "negative",
      sensitivity: 0.90,
      revenueAtRisk: 7_650_000_000,
      revenueAtRiskPercent: 15.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-006",
      eventId: "evt-008",
      eventTitle: "Red Sea Shipping Disruption Escalation",
      exposureType: "revenue",
      exposureDirection: "positive",
      sensitivity: 0.95,
      revenueAtRisk: 10_200_000_000,
      revenueAtRiskPercent: 20.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-007",
      eventId: "evt-004",
      eventTitle: "OPEC+ Production Cut Extension",
      exposureType: "operational",
      exposureDirection: "negative",
      sensitivity: 0.50,
      revenueAtRisk: 2_040_000_000,
      revenueAtRiskPercent: 4.0,
      hedgeRecommendation: "traditional",
    },
  ],
  "comp-003": [
    {
      id: "exp-008",
      eventId: "evt-003",
      eventTitle: "China-Taiwan Military Escalation",
      exposureType: "operational",
      exposureDirection: "negative",
      sensitivity: 0.99,
      revenueAtRisk: 78_390_000_000,
      revenueAtRiskPercent: 90.0,
      hedgeRecommendation: "blend",
    },
    {
      id: "exp-009",
      eventId: "evt-007",
      eventTitle: "US Semiconductor Export Controls Expansion",
      exposureType: "revenue",
      exposureDirection: "negative",
      sensitivity: 0.70,
      revenueAtRisk: 8_710_000_000,
      revenueAtRiskPercent: 10.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-010",
      eventId: "evt-002",
      eventTitle: "EU Carbon Border Tax Expansion",
      exposureType: "regulatory",
      exposureDirection: "negative",
      sensitivity: 0.25,
      revenueAtRisk: 1_742_000_000,
      revenueAtRiskPercent: 2.0,
      hedgeRecommendation: "no_hedge",
    },
  ],
  "comp-004": [
    {
      id: "exp-011",
      eventId: "evt-002",
      eventTitle: "EU Carbon Border Tax Expansion",
      exposureType: "regulatory",
      exposureDirection: "negative",
      sensitivity: 0.82,
      revenueAtRisk: 10_335_000_000,
      revenueAtRiskPercent: 15.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-012",
      eventId: "evt-001",
      eventTitle: "Iran Strait of Hormuz Disruption",
      exposureType: "supply_chain",
      exposureDirection: "negative",
      sensitivity: 0.65,
      revenueAtRisk: 6_890_000_000,
      revenueAtRiskPercent: 10.0,
      hedgeRecommendation: "blend",
    },
    {
      id: "exp-013",
      eventId: "evt-006",
      eventTitle: "Russia-Ukraine Ceasefire Agreement",
      exposureType: "operational",
      exposureDirection: "positive",
      sensitivity: 0.60,
      revenueAtRisk: 6_890_000_000,
      revenueAtRiskPercent: 10.0,
      hedgeRecommendation: "traditional",
    },
  ],
  "comp-005": [
    {
      id: "exp-014",
      eventId: "evt-003",
      eventTitle: "China-Taiwan Military Escalation",
      exposureType: "supply_chain",
      exposureDirection: "negative",
      sensitivity: 0.88,
      revenueAtRisk: 57_495_000_000,
      revenueAtRiskPercent: 15.0,
      hedgeRecommendation: "blend",
    },
    {
      id: "exp-015",
      eventId: "evt-007",
      eventTitle: "US Semiconductor Export Controls Expansion",
      exposureType: "revenue",
      exposureDirection: "negative",
      sensitivity: 0.55,
      revenueAtRisk: 15_332_000_000,
      revenueAtRiskPercent: 4.0,
      hedgeRecommendation: "prediction_market",
    },
    {
      id: "exp-016",
      eventId: "evt-005",
      eventTitle: "US TikTok Ban Implementation",
      exposureType: "revenue",
      exposureDirection: "negative",
      sensitivity: 0.30,
      revenueAtRisk: 3_833_000_000,
      revenueAtRiskPercent: 1.0,
      hedgeRecommendation: "no_hedge",
    },
  ],
};

// ─── Hedge Comparisons ───────────────────────────────────────────────────────

export const mockHedgeComparisons: HedgeComparison[] = [
  {
    id: "hedge-001",
    eventId: "evt-001",
    eventTitle: "Iran Strait of Hormuz Disruption",
    companyId: "comp-001",
    companyName: "ExxonMobil",
    predictionMarket: {
      cost: 3_100_000,
      payout: 10_000_000,
      roi: 2.23,
      instrument: "Binary contract: Hormuz blockade by Q3 2026",
      platform: "Polymarket",
    },
    traditional: {
      cost: 4_500_000,
      payout: 10_000_000,
      roi: 1.22,
      instrument: "Brent crude put options (6-month)",
      provider: "Goldman Sachs",
    },
    recommendation: "prediction_market",
    savingsPercent: 31.1,
  },
  {
    id: "hedge-002",
    eventId: "evt-001",
    eventTitle: "Iran Strait of Hormuz Disruption",
    companyId: "comp-002",
    companyName: "Maersk",
    predictionMarket: {
      cost: 2_200_000,
      payout: 7_500_000,
      roi: 2.41,
      instrument: "Binary contract: Hormuz disruption",
      platform: "Polymarket",
    },
    traditional: {
      cost: 3_800_000,
      payout: 7_500_000,
      roi: 0.97,
      instrument: "Freight rate forward agreements",
      provider: "Clarksons",
    },
    recommendation: "prediction_market",
    savingsPercent: 42.1,
  },
  {
    id: "hedge-003",
    eventId: "evt-002",
    eventTitle: "EU Carbon Border Tax Expansion",
    companyId: "comp-004",
    companyName: "BASF",
    predictionMarket: {
      cost: 5_200_000,
      payout: 12_000_000,
      roi: 1.31,
      instrument: "Binary contract: CBAM expansion by 2027",
      platform: "Metaculus",
    },
    traditional: {
      cost: 7_100_000,
      payout: 12_000_000,
      roi: 0.69,
      instrument: "EU ETS carbon credit futures",
      provider: "ICE Futures Europe",
    },
    recommendation: "prediction_market",
    savingsPercent: 26.8,
  },
  {
    id: "hedge-004",
    eventId: "evt-003",
    eventTitle: "China-Taiwan Military Escalation",
    companyId: "comp-003",
    companyName: "TSMC",
    predictionMarket: {
      cost: 850_000,
      payout: 15_000_000,
      roi: 16.65,
      instrument: "Binary contract: PLA military action Taiwan",
      platform: "Metaculus",
    },
    traditional: {
      cost: 1_200_000,
      payout: 15_000_000,
      roi: 11.5,
      instrument: "SOXX semiconductor ETF put options (12-month)",
      provider: "Morgan Stanley",
    },
    recommendation: "blend",
    savingsPercent: 29.2,
  },
  {
    id: "hedge-005",
    eventId: "evt-003",
    eventTitle: "China-Taiwan Military Escalation",
    companyId: "comp-005",
    companyName: "Apple",
    predictionMarket: {
      cost: 1_600_000,
      payout: 25_000_000,
      roi: 14.63,
      instrument: "Binary contract: Taiwan strait closure",
      platform: "Polymarket",
    },
    traditional: {
      cost: 2_400_000,
      payout: 25_000_000,
      roi: 9.42,
      instrument: "AAPL put spreads + supply chain insurance",
      provider: "JP Morgan",
    },
    recommendation: "blend",
    savingsPercent: 33.3,
  },
  {
    id: "hedge-006",
    eventId: "evt-004",
    eventTitle: "OPEC+ Production Cut Extension",
    companyId: "comp-002",
    companyName: "Maersk",
    predictionMarket: {
      cost: 1_400_000,
      payout: 4_000_000,
      roi: 1.86,
      instrument: "Binary contract: OPEC cuts extended Q4 2026",
      platform: "Kalshi",
    },
    traditional: {
      cost: 1_900_000,
      payout: 4_000_000,
      roi: 1.11,
      instrument: "Bunker fuel swap agreements (6-month)",
      provider: "Vitol",
    },
    recommendation: "prediction_market",
    savingsPercent: 26.3,
  },
  {
    id: "hedge-007",
    eventId: "evt-007",
    eventTitle: "US Semiconductor Export Controls Expansion",
    companyId: "comp-003",
    companyName: "TSMC",
    predictionMarket: {
      cost: 3_800_000,
      payout: 10_000_000,
      roi: 1.63,
      instrument: "Binary contract: expanded chip export controls 2026",
      platform: "Kalshi",
    },
    traditional: {
      cost: 5_600_000,
      payout: 10_000_000,
      roi: 0.79,
      instrument: "Revenue insurance + FX hedges (USD/TWD)",
      provider: "AIG",
    },
    recommendation: "prediction_market",
    savingsPercent: 32.1,
  },
  {
    id: "hedge-008",
    eventId: "evt-007",
    eventTitle: "US Semiconductor Export Controls Expansion",
    companyId: "comp-005",
    companyName: "Apple",
    predictionMarket: {
      cost: 2_900_000,
      payout: 8_000_000,
      roi: 1.76,
      instrument: "Binary contract: chip export controls expansion",
      platform: "Kalshi",
    },
    traditional: {
      cost: 4_100_000,
      payout: 8_000_000,
      roi: 0.95,
      instrument: "Sector ETF puts + supply chain diversification fund",
      provider: "BlackRock",
    },
    recommendation: "prediction_market",
    savingsPercent: 29.3,
  },
  {
    id: "hedge-009",
    eventId: "evt-008",
    eventTitle: "Red Sea Shipping Disruption Escalation",
    companyId: "comp-002",
    companyName: "Maersk",
    predictionMarket: {
      cost: 4_100_000,
      payout: 12_000_000,
      roi: 1.93,
      instrument: "Binary contract: Red Sea full closure 2026",
      platform: "Polymarket",
    },
    traditional: {
      cost: 5_800_000,
      payout: 12_000_000,
      roi: 1.07,
      instrument: "Freight derivatives (containerized FFA)",
      provider: "Clarksons",
    },
    recommendation: "prediction_market",
    savingsPercent: 29.3,
  },
  {
    id: "hedge-010",
    eventId: "evt-006",
    eventTitle: "Russia-Ukraine Ceasefire Agreement",
    companyId: "comp-004",
    companyName: "BASF",
    predictionMarket: {
      cost: 1_800_000,
      payout: 8_000_000,
      roi: 3.44,
      instrument: "Binary contract: ceasefire by end of 2026",
      platform: "Metaculus",
    },
    traditional: {
      cost: 2_500_000,
      payout: 8_000_000,
      roi: 2.2,
      instrument: "European natural gas futures (TTF)",
      provider: "ICE Futures Europe",
    },
    recommendation: "prediction_market",
    savingsPercent: 28.0,
  },
  {
    id: "hedge-011",
    eventId: "evt-001",
    eventTitle: "Iran Strait of Hormuz Disruption",
    companyId: "comp-004",
    companyName: "BASF",
    predictionMarket: {
      cost: 2_700_000,
      payout: 8_500_000,
      roi: 2.15,
      instrument: "Binary contract: Hormuz disruption",
      platform: "Polymarket",
    },
    traditional: {
      cost: 3_900_000,
      payout: 8_500_000,
      roi: 1.18,
      instrument: "Naphtha feedstock forward contracts",
      provider: "Shell Trading",
    },
    recommendation: "prediction_market",
    savingsPercent: 30.8,
  },
  {
    id: "hedge-012",
    eventId: "evt-002",
    eventTitle: "EU Carbon Border Tax Expansion",
    companyId: "comp-003",
    companyName: "TSMC",
    predictionMarket: {
      cost: 680_000,
      payout: 2_000_000,
      roi: 1.94,
      instrument: "Binary contract: CBAM expansion",
      platform: "Metaculus",
    },
    traditional: {
      cost: 950_000,
      payout: 2_000_000,
      roi: 1.11,
      instrument: "EU regulatory compliance insurance",
      provider: "Allianz",
    },
    recommendation: "no_hedge",
    savingsPercent: 28.4,
  },
];

// ─── Lookup Functions ────────────────────────────────────────────────────────

export function getEventById(id: string): GeopoliticalEvent | undefined {
  return mockEvents.find((e) => e.id === id);
}

export function getCompanyById(id: string): Company | undefined {
  return mockCompanies.find((c) => c.id === id);
}

export function getCompanyExposures(companyId: string): CompanyExposure[] {
  return mockExposures[companyId] || [];
}

export function getHedgeComparisonsForEvent(eventId: string): HedgeComparison[] {
  return mockHedgeComparisons.filter((h) => h.eventId === eventId);
}
