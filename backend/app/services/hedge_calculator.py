def calculate_pm_hedge(probability: float, notional: float) -> dict:
    """Calculate prediction market hedge costs and returns."""
    cost = probability * notional
    payout = notional
    roi = (payout - cost) / cost if cost > 0 else 0
    return {"cost": round(cost, 2), "payout": round(payout, 2), "roi": round(roi, 4)}


def calculate_traditional_hedge(category: str, notional: float, probability: float) -> dict:
    """Map event category to traditional instrument and calculate costs."""
    instrument_map = {
        "trade": {"instrument": "FX Forward", "spread": 0.02, "premium_factor": 0.15},
        "conflict": {"instrument": "Oil Futures Put", "spread": 0.03, "premium_factor": 0.20},
        "regulatory": {
            "instrument": "Sector ETF Put Option",
            "spread": 0.025,
            "premium_factor": 0.18,
        },
        "climate": {"instrument": "Catastrophe Bond", "spread": 0.04, "premium_factor": 0.25},
        "geopolitical": {
            "instrument": "Commodity Futures Spread",
            "spread": 0.03,
            "premium_factor": 0.22,
        },
        "economic": {
            "instrument": "Interest Rate Swap",
            "spread": 0.015,
            "premium_factor": 0.12,
        },
    }
    params = instrument_map.get(category, instrument_map["geopolitical"])
    cost = notional * (params["spread"] + params["premium_factor"] * probability)
    payout = notional * 0.85  # typical recovery
    roi = (payout - cost) / cost if cost > 0 else 0
    return {
        "instrument": params["instrument"],
        "cost": round(cost, 2),
        "payout": round(payout, 2),
        "roi": round(roi, 4),
    }


def recommend_hedge(pm_roi: float, trad_roi: float, probability: float) -> str:
    """Recommend a hedging strategy based on ROI comparison and probability."""
    if probability < 0.05:
        return "no_hedge"
    if pm_roi > trad_roi * 1.3:
        return "prediction_market"
    if trad_roi > pm_roi * 1.3:
        return "traditional"
    return "blend"
