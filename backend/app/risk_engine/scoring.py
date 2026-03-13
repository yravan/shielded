"""Risk scoring functions.

This is where risk modeling lives and evolves. Today it's a simple
weighted formula; it can be iterated toward proper risk models
(Monte Carlo, correlation matrices, VaR, tail risk) without
touching the rest of the system.
"""

from .types import CompanyRiskResult, ExposureMatch


def normalize_probability(value: float) -> float:
    """Normalize a probability value to 0-1 range."""
    if value > 1:
        value = value / 100.0
    return max(0.0, min(1.0, value))


def event_relevance_score(
    probability: float,
    exposure_weight: float,
    keyword_hits: int = 1,
) -> int:
    """Combine probability, exposure weight, and keyword hits into a 0-100 score.

    v1: simple weighted formula
      - 45% from event probability
      - 45% from company exposure weight (normalized to 0-1)
      - 10% from keyword hit density

    Future: could incorporate event correlation, historical base rates,
    volatility-adjusted probabilities, etc.
    """
    prob_component = normalize_probability(probability) * 100
    exposure_component = max(0.0, min(10.0, float(exposure_weight))) / 10.0
    hit_boost = min(1.0, keyword_hits / 4)
    score = prob_component * (0.45 + 0.45 * exposure_component + 0.10 * hit_boost)
    return int(round(max(0.0, min(100.0, score))))


def aggregate_risk_score(relevance_scores: list[int]) -> int:
    """Compute aggregate risk score from individual event relevance scores.

    v1: weighted blend of average (70%) and peak (30%) scores.
    The peak component ensures tail risks aren't averaged away.

    Future: could use copula models, diversification adjustments,
    correlation-based aggregation, etc.
    """
    scores = [max(0, min(100, s)) for s in relevance_scores]
    if not scores:
        return 0
    avg_score = sum(scores) / len(scores)
    peak_score = max(scores)
    return int(round(0.7 * avg_score + 0.3 * peak_score))


def compute_company_risk(
    company_id: str,
    matches: list[ExposureMatch],
) -> CompanyRiskResult:
    """Roll up all event matches into a single company risk result."""
    if not matches:
        return CompanyRiskResult(
            company_id=company_id,
            risk_score=0,
            avg_score=0.0,
            peak_score=0,
            event_count=0,
        )

    scores = [m.relevance_score for m in matches]
    risk_score = aggregate_risk_score(scores)
    avg = sum(scores) / len(scores)
    peak = max(scores)

    return CompanyRiskResult(
        company_id=company_id,
        risk_score=risk_score,
        avg_score=round(avg, 1),
        peak_score=peak,
        event_count=len(matches),
    )
