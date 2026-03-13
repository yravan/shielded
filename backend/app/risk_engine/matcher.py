"""Event-to-company matching engine.

Scores how relevant a geopolitical/macro event is to a given company
based on theme overlap with the company's exposure profile.
"""

from .scoring import event_relevance_score
from .themes import THEME_KEYWORDS, extract_themes
from .types import CompanyInput, EventInput, ExposureMatch


def score_event_for_company(
    event: EventInput,
    company: CompanyInput,
) -> ExposureMatch:
    """Score how relevant an event is to a specific company.

    1. Extract themes from the event text
    2. For each theme, find the best-matching exposure label in the
       company's exposure profile using keyword overlap
    3. Combine probability, exposure weights, and keyword hits into
       a 0-100 relevance score
    """
    themes = extract_themes(event)
    if not themes:
        return ExposureMatch(
            relevance_score=0,
            matched_themes=[],
            explanation="No theme overlap detected.",
        )

    exposure_text = {key.lower(): value for key, value in company.exposures.items()}

    exposure_hits: list[tuple[str, float, int]] = []
    for theme in themes:
        keywords = THEME_KEYWORDS.get(theme, [])
        best_weight = 0.0
        best_hits = 0
        for label, weight in exposure_text.items():
            hit_count = sum(1 for kw in keywords if kw in label)
            if hit_count > best_hits:
                best_hits = hit_count
                best_weight = weight
        if best_hits == 0:
            # Soft match: theme matched event but no direct exposure label hit.
            # Use a modest fraction of the company's average exposure weight.
            values = list(company.exposures.values())
            avg_weight = sum(values) / max(1, len(values))
            best_weight = round(avg_weight * 0.6, 1)
            best_hits = 1
        exposure_hits.append((theme, best_weight, best_hits))

    avg_weight = sum(w for _, w, _ in exposure_hits) / len(exposure_hits)
    total_hits = sum(h for _, _, h in exposure_hits)
    score = event_relevance_score(event.probability, avg_weight, keyword_hits=total_hits)

    explain_parts = [
        f"{theme.replace('_', ' ')} (weight={weight})"
        for theme, weight, _ in exposure_hits
    ]
    explanation = f"Matched themes for {company.ticker}: " + ", ".join(explain_parts)

    return ExposureMatch(
        relevance_score=score,
        matched_themes=themes,
        explanation=explanation,
    )


def match_event_to_companies(
    event: EventInput,
    companies: list[CompanyInput],
    min_score: int = 20,
) -> list[tuple[str, ExposureMatch]]:
    """Match an event against all companies, returning those above threshold.

    Returns a list of (company_id, ExposureMatch) tuples sorted by
    relevance score descending.
    """
    matches: list[tuple[str, ExposureMatch]] = []
    for company in companies:
        result = score_event_for_company(event, company)
        if result.relevance_score >= min_score:
            matches.append((company.company_id, result))

    matches.sort(key=lambda item: item[1].relevance_score, reverse=True)
    return matches
