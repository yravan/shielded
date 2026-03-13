"""Theme-based impact percentage estimates.

Maps geopolitical themes to estimated revenue/OPEX/CAPEX impact
percentages.  These are starting estimates that Andre can tune based on
historical data, research, and domain expertise.
"""

THEME_IMPACT_ESTIMATES: dict[str, dict[str, float]] = {
    "taiwan_china_conflict": {"revenue": 0.15, "opex": 0.10, "capex": 0.20},
    "export_controls":       {"revenue": 0.10, "opex": 0.05, "capex": 0.08},
    "recession":             {"revenue": 0.12, "opex": 0.08, "capex": 0.15},
    "oil_shock":             {"revenue": 0.08, "opex": 0.15, "capex": 0.05},
    "semiconductor":         {"revenue": 0.12, "opex": 0.08, "capex": 0.18},
    "shipping":              {"revenue": 0.06, "opex": 0.10, "capex": 0.03},
    "tariff":                {"revenue": 0.10, "opex": 0.08, "capex": 0.04},
    "inflation":             {"revenue": 0.05, "opex": 0.12, "capex": 0.10},
    "interest_rate":         {"revenue": 0.04, "opex": 0.03, "capex": 0.12},
    "climate":               {"revenue": 0.08, "opex": 0.10, "capex": 0.15},
    "regulation":            {"revenue": 0.06, "opex": 0.08, "capex": 0.05},
    "cyber":                 {"revenue": 0.08, "opex": 0.12, "capex": 0.03},
    "middle_east":           {"revenue": 0.10, "opex": 0.12, "capex": 0.06},
    "russia_ukraine":        {"revenue": 0.08, "opex": 0.10, "capex": 0.08},
}

# Fallback for themes not in the map
_DEFAULT_ESTIMATE = {"revenue": 0.05, "opex": 0.05, "capex": 0.05}


def estimate_impact_pcts(
    matched_themes: list[str],
    exposure_weight: float,
) -> dict[str, float]:
    """Average impact percentages across matched themes, scaled by exposure weight.

    Args:
        matched_themes: List of theme keys (e.g. ["recession", "oil_shock"]).
        exposure_weight: Relevance score on 0-100 scale (from the matcher).

    Returns:
        {"revenue_impact_pct": float, "opex_impact_pct": float, "capex_impact_pct": float}
    """
    if not matched_themes:
        return {
            "revenue_impact_pct": 0.0,
            "opex_impact_pct": 0.0,
            "capex_impact_pct": 0.0,
        }

    # Normalize weight from 0-100 to 0-1
    weight_factor = min(max(exposure_weight, 0), 100) / 100.0

    rev_sum = 0.0
    opex_sum = 0.0
    capex_sum = 0.0

    for theme in matched_themes:
        est = THEME_IMPACT_ESTIMATES.get(theme, _DEFAULT_ESTIMATE)
        rev_sum += est["revenue"]
        opex_sum += est["opex"]
        capex_sum += est["capex"]

    n = len(matched_themes)
    return {
        "revenue_impact_pct": round(rev_sum / n * weight_factor, 4),
        "opex_impact_pct": round(opex_sum / n * weight_factor, 4),
        "capex_impact_pct": round(capex_sum / n * weight_factor, 4),
    }
