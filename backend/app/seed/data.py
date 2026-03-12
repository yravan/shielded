"""Static seed data matching the frontend mock data."""

EVENTS = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "title": "US-China Tariff Escalation Beyond 60%",
        "description": (
            "Will the United States impose tariffs exceeding 60% on Chinese imports "
            "by the end of 2026? This market tracks the probability of a significant "
            "escalation in US-China trade tensions through tariff increases."
        ),
        "category": "trade",
        "region": "Asia-Pacific",
        "source": "polymarket",
        "source_id": "pm-us-china-tariff-60",
        "source_url": "https://polymarket.com/event/us-china-tariff",
        "current_probability": 0.42,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567802",
        "title": "EU Carbon Border Tax Implementation by 2027",
        "description": (
            "Will the European Union fully implement its Carbon Border Adjustment "
            "Mechanism (CBAM) with enforcement by 2027? This tracks the regulatory "
            "risk for companies exporting carbon-intensive goods to the EU."
        ),
        "category": "regulatory",
        "region": "Europe",
        "source": "metaculus",
        "source_id": "mc-eu-cbam-2027",
        "source_url": "https://www.metaculus.com/questions/eu-cbam",
        "current_probability": 0.71,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567803",
        "title": "Taiwan Strait Military Confrontation in 2026",
        "description": (
            "Will there be a significant military confrontation in the Taiwan Strait "
            "during 2026? Includes naval blockades, airspace incursions, or direct "
            "military engagement between China and Taiwan/allied forces."
        ),
        "category": "conflict",
        "region": "Asia-Pacific",
        "source": "polymarket",
        "source_id": "pm-taiwan-conflict-2026",
        "source_url": "https://polymarket.com/event/taiwan-strait",
        "current_probability": 0.08,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
        "title": "OPEC+ Production Cut Extension Through 2026",
        "description": (
            "Will OPEC+ extend its current production cuts through the end of 2026? "
            "This affects global oil supply and prices, impacting energy costs for "
            "manufacturing and transportation sectors."
        ),
        "category": "economic",
        "region": "Middle East",
        "source": "kalshi",
        "source_id": "kl-opec-cuts-2026",
        "source_url": "https://kalshi.com/events/opec-cuts",
        "current_probability": 0.63,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567805",
        "title": "US Federal Reserve Rate Below 3% by End of 2026",
        "description": (
            "Will the US Federal Reserve's federal funds rate fall below 3% "
            "by December 31, 2026? Tracks monetary policy trajectory and its "
            "impact on borrowing costs and capital expenditure."
        ),
        "category": "economic",
        "region": "North America",
        "source": "kalshi",
        "source_id": "kl-fed-rate-3pct",
        "source_url": "https://kalshi.com/events/fed-rate",
        "current_probability": 0.35,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567806",
        "title": "Major Semiconductor Export Ban Expansion",
        "description": (
            "Will the US or EU expand semiconductor export bans to additional "
            "countries or chip categories by mid-2026? Tracks technology "
            "decoupling risks affecting the global chip supply chain."
        ),
        "category": "trade",
        "region": "Global",
        "source": "polymarket",
        "source_id": "pm-chip-export-ban",
        "source_url": "https://polymarket.com/event/chip-ban",
        "current_probability": 0.55,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567807",
        "title": "Arctic Shipping Route Commercially Viable by 2028",
        "description": (
            "Will the Northern Sea Route become commercially viable for regular "
            "container shipping by 2028? Climate change is opening Arctic passages, "
            "potentially disrupting traditional shipping lanes and logistics."
        ),
        "category": "climate",
        "region": "Global",
        "source": "metaculus",
        "source_id": "mc-arctic-shipping-2028",
        "source_url": "https://www.metaculus.com/questions/arctic-route",
        "current_probability": 0.22,
        "status": "active",
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567808",
        "title": "Russia-Ukraine Ceasefire Agreement in 2026",
        "description": (
            "Will Russia and Ukraine reach a formal ceasefire or peace agreement "
            "during 2026? Resolution of this conflict would significantly impact "
            "European energy markets, grain supply chains, and defense spending."
        ),
        "category": "conflict",
        "region": "Europe",
        "source": "polymarket",
        "source_id": "pm-russia-ukraine-ceasefire",
        "source_url": "https://polymarket.com/event/russia-ukraine-peace",
        "current_probability": 0.18,
        "status": "active",
    },
]

COMPANIES = [
    {
        "id": "b1c2d3e4-f5a6-7890-bcde-fa1234567801",
        "name": "Apex Manufacturing Corp",
        "ticker": "APEX",
        "sector": "Industrials",
        "annual_revenue": 4200000000.00,
        "operating_expense": 3150000000.00,
        "capital_expense": 630000000.00,
    },
    {
        "id": "b1c2d3e4-f5a6-7890-bcde-fa1234567802",
        "name": "GlobalTech Solutions",
        "ticker": "GLTK",
        "sector": "Technology",
        "annual_revenue": 8500000000.00,
        "operating_expense": 5950000000.00,
        "capital_expense": 1700000000.00,
    },
    {
        "id": "b1c2d3e4-f5a6-7890-bcde-fa1234567803",
        "name": "Pacific Energy Holdings",
        "ticker": "PCEH",
        "sector": "Energy",
        "annual_revenue": 12000000000.00,
        "operating_expense": 9600000000.00,
        "capital_expense": 2400000000.00,
    },
    {
        "id": "b1c2d3e4-f5a6-7890-bcde-fa1234567804",
        "name": "TransOcean Logistics",
        "ticker": "TOCL",
        "sector": "Transportation",
        "annual_revenue": 3100000000.00,
        "operating_expense": 2635000000.00,
        "capital_expense": 465000000.00,
    },
    {
        "id": "b1c2d3e4-f5a6-7890-bcde-fa1234567805",
        "name": "Meridian Pharmaceuticals",
        "ticker": "MRDP",
        "sector": "Healthcare",
        "annual_revenue": 6800000000.00,
        "operating_expense": 4760000000.00,
        "capital_expense": 1360000000.00,
    },
]

EXPOSURES = [
    # Apex Manufacturing - exposed to tariffs, OPEC, Taiwan
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567801",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567801",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "exposure_type": "supply_chain",
        "exposure_direction": "negative",
        "sensitivity": 0.75,
        "revenue_impact_pct": 0.12,
        "opex_impact_pct": 0.08,
        "capex_impact_pct": 0.05,
        "notes": "Heavy reliance on Chinese-sourced components; 30% of supply chain exposed",
    },
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567802",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567801",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
        "exposure_type": "operational",
        "exposure_direction": "negative",
        "sensitivity": 0.50,
        "revenue_impact_pct": 0.03,
        "opex_impact_pct": 0.15,
        "capex_impact_pct": 0.02,
        "notes": "Energy-intensive manufacturing; OPEC cuts raise operational costs",
    },
    # GlobalTech - exposed to chip ban, Taiwan, tariffs
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567803",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567802",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567806",
        "exposure_type": "supply_chain",
        "exposure_direction": "negative",
        "sensitivity": 0.90,
        "revenue_impact_pct": 0.20,
        "opex_impact_pct": 0.10,
        "capex_impact_pct": 0.15,
        "notes": "Core products depend on advanced semiconductor supply; critical exposure",
    },
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567804",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567802",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567803",
        "exposure_type": "supply_chain",
        "exposure_direction": "negative",
        "sensitivity": 0.85,
        "revenue_impact_pct": 0.25,
        "opex_impact_pct": 0.05,
        "capex_impact_pct": 0.10,
        "notes": "TSMC foundry concentration; Taiwan conflict would cripple supply",
    },
    # Pacific Energy - exposed to OPEC, Russia-Ukraine, climate
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567805",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567803",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
        "exposure_type": "revenue",
        "exposure_direction": "positive",
        "sensitivity": 0.80,
        "revenue_impact_pct": 0.18,
        "opex_impact_pct": 0.04,
        "capex_impact_pct": 0.03,
        "notes": "Production cuts raise oil prices; positive revenue impact for producer",
    },
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567806",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567803",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567808",
        "exposure_type": "revenue",
        "exposure_direction": "mixed",
        "sensitivity": 0.60,
        "revenue_impact_pct": 0.10,
        "opex_impact_pct": 0.05,
        "capex_impact_pct": 0.08,
        "notes": "Ceasefire would normalize European energy markets; mixed for US energy",
    },
    # TransOcean Logistics - exposed to Arctic shipping, tariffs, OPEC
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567807",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567804",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567807",
        "exposure_type": "operational",
        "exposure_direction": "mixed",
        "sensitivity": 0.65,
        "revenue_impact_pct": 0.08,
        "opex_impact_pct": 0.12,
        "capex_impact_pct": 0.20,
        "notes": "New Arctic routes create opportunity but require fleet investment",
    },
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567808",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567804",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "exposure_type": "revenue",
        "exposure_direction": "negative",
        "sensitivity": 0.55,
        "revenue_impact_pct": 0.15,
        "opex_impact_pct": 0.06,
        "capex_impact_pct": 0.03,
        "notes": "Tariff escalation reduces trade volumes on Asia-Pacific routes",
    },
    # Meridian Pharmaceuticals - exposed to EU regulatory, tariffs, Fed rate
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567809",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567805",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567802",
        "exposure_type": "regulatory",
        "exposure_direction": "negative",
        "sensitivity": 0.70,
        "revenue_impact_pct": 0.06,
        "opex_impact_pct": 0.10,
        "capex_impact_pct": 0.04,
        "notes": "CBAM increases cost of API imports and carbon compliance burden",
    },
    {
        "id": "c1d2e3f4-a5b6-7890-cdef-ab1234567810",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567805",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567805",
        "exposure_type": "operational",
        "exposure_direction": "positive",
        "sensitivity": 0.45,
        "revenue_impact_pct": 0.02,
        "opex_impact_pct": 0.03,
        "capex_impact_pct": 0.08,
        "notes": "Lower rates reduce borrowing costs for R&D capital investments",
    },
]

HEDGE_ANALYSES = [
    {
        "id": "d1e2f3a4-b5c6-7890-defa-bc1234567801",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567801",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "pm_cost": 158760.00,
        "pm_payout": 378000.00,
        "pm_roi": 1.3812,
        "traditional_instrument": "FX Forward",
        "traditional_cost": 64260.00,
        "traditional_payout": 321300.00,
        "traditional_roi": 3.9993,
        "recommendation": "traditional",
        "savings_percent": -147.00,
        "notes": "Traditional FX forward more cost-effective at current probability",
    },
    {
        "id": "d1e2f3a4-b5c6-7890-defa-bc1234567802",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567802",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567806",
        "pm_cost": 841500.00,
        "pm_payout": 1530000.00,
        "pm_roi": 0.8180,
        "traditional_instrument": "Commodity Futures Spread",
        "traditional_cost": 226710.00,
        "traditional_payout": 1300500.00,
        "traditional_roi": 4.7365,
        "recommendation": "traditional",
        "savings_percent": -271.31,
        "notes": "High sensitivity makes traditional hedge significantly more efficient",
    },
    {
        "id": "d1e2f3a4-b5c6-7890-defa-bc1234567803",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567802",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567803",
        "pm_cost": 144500.00,
        "pm_payout": 1806250.00,
        "pm_roi": 11.4983,
        "traditional_instrument": "Oil Futures Put",
        "traditional_cost": 83137.50,
        "traditional_payout": 1535312.50,
        "traditional_roi": 17.4684,
        "recommendation": "blend",
        "savings_percent": -73.82,
        "notes": "Low probability event; both instruments provide good asymmetric payoff",
    },
    {
        "id": "d1e2f3a4-b5c6-7890-defa-bc1234567804",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567803",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
        "pm_cost": 1088640.00,
        "pm_payout": 1728000.00,
        "pm_roi": 0.5873,
        "traditional_instrument": "Interest Rate Swap",
        "traditional_cost": 156816.00,
        "traditional_payout": 1468800.00,
        "traditional_roi": 8.3658,
        "recommendation": "traditional",
        "savings_percent": -594.15,
        "notes": "Energy producer benefits from production cuts; hedge against reversal",
    },
    {
        "id": "d1e2f3a4-b5c6-7890-defa-bc1234567805",
        "company_id": "b1c2d3e4-f5a6-7890-bcde-fa1234567804",
        "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567807",
        "pm_cost": 35464.00,
        "pm_payout": 161200.00,
        "pm_roi": 3.5455,
        "traditional_instrument": "Catastrophe Bond",
        "traditional_cost": 15493.60,
        "traditional_payout": 137020.00,
        "traditional_roi": 7.8435,
        "recommendation": "traditional",
        "savings_percent": -128.87,
        "notes": "Climate-related event; catastrophe bond provides better coverage",
    },
]
