from app.schemas.impact import ScenarioPoint


def calculate_scenarios(
    annual_revenue: float,
    operating_expense: float,
    capital_expense: float,
    revenue_impact_pct: float,
    opex_impact_pct: float,
    capex_impact_pct: float,
    sensitivity: float,
) -> list[ScenarioPoint]:
    """Calculate scenario analysis for a company-event pair.

    For each probability from 0.0 to 1.0 in 0.1 steps, compute the
    financial impact on revenue, opex, and capex.
    """
    scenarios = []
    for i in range(11):
        probability = round(i * 0.1, 1)
        revenue_impact = round(
            annual_revenue * revenue_impact_pct * probability * sensitivity, 2
        )
        opex_impact = round(
            operating_expense * opex_impact_pct * probability * sensitivity, 2
        )
        capex_impact = round(
            capital_expense * capex_impact_pct * probability * sensitivity, 2
        )
        total_impact = round(revenue_impact + opex_impact + capex_impact, 2)

        scenarios.append(
            ScenarioPoint(
                probability=probability,
                revenue_impact=revenue_impact,
                opex_impact=opex_impact,
                capex_impact=capex_impact,
                total_impact=total_impact,
            )
        )

    return scenarios
