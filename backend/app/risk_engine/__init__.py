"""Risk Engine — event-to-company matching and risk scoring.

This package is intentionally framework-free. It uses only Python
stdlib and has no dependencies on SQLAlchemy, FastAPI, Celery, or
any other infrastructure code.

Public API:
    extract_themes(event) → list[str]
    score_event_for_company(event, company) → ExposureMatch
    match_event_to_companies(event, companies) → list[(company_id, ExposureMatch)]
    compute_company_risk(company_id, matches) → CompanyRiskResult
    get_default_risk_profile(sector) → dict[str, int]
"""

from .hedges import HedgeInstrument, get_hedge_instruments
from .impact_estimates import estimate_impact_pcts
from .matcher import match_event_to_companies, score_event_for_company
from .scoring import aggregate_risk_score, compute_company_risk
from .sector_defaults import get_default_risk_profile
from .themes import THEME_KEYWORDS, extract_themes
from .types import CompanyInput, CompanyRiskResult, EventInput, ExposureMatch

__all__ = [
    "EventInput",
    "CompanyInput",
    "ExposureMatch",
    "CompanyRiskResult",
    "HedgeInstrument",
    "extract_themes",
    "THEME_KEYWORDS",
    "score_event_for_company",
    "match_event_to_companies",
    "aggregate_risk_score",
    "compute_company_risk",
    "get_default_risk_profile",
    "estimate_impact_pcts",
    "get_hedge_instruments",
]
