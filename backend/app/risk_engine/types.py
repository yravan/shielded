"""Pure data types for the risk engine. No framework dependencies."""

from dataclasses import dataclass, field


@dataclass
class EventInput:
    """Minimal event representation for risk scoring."""

    title: str
    description: str
    category: str
    tags: list[str]
    probability: float


@dataclass
class CompanyInput:
    """Minimal company representation for risk scoring."""

    company_id: str
    ticker: str
    sector: str
    exposures: dict[str, float]  # label → weight (0-10)


@dataclass
class ExposureMatch:
    """Result of matching a single event to a single company."""

    relevance_score: int  # 0-100
    matched_themes: list[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class CompanyRiskResult:
    """Aggregate risk assessment for a company across all matched events."""

    company_id: str
    risk_score: int  # 0-100
    avg_score: float
    peak_score: int
    event_count: int
