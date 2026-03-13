"""Theme extraction from event text using keyword matching.

This module maps event text to risk themes. Each theme represents
a category of geopolitical/macro risk that can affect companies.

To add a new theme: add an entry to THEME_KEYWORDS with the theme
name and a list of keywords to match against.
"""

from .types import EventInput

THEME_KEYWORDS: dict[str, list[str]] = {
    "taiwan_china_conflict": [
        "taiwan",
        "china",
        "strait",
        "military",
        "conflict",
        "invasion",
        "pla",
        "reunification",
    ],
    "export_controls": [
        "export controls",
        "export control",
        "sanction",
        "restriction",
        "chip ban",
        "entity list",
        "blacklist",
        "trade restriction",
        "embargo",
    ],
    "recession": [
        "recession",
        "slowdown",
        "demand",
        "risk-off",
        "unemployment",
        "contraction",
        "downturn",
        "gdp decline",
    ],
    "oil_shock": [
        "oil",
        "crude",
        "energy shock",
        "opec",
        "petroleum",
        "brent",
        "wti",
    ],
    "semiconductor": [
        "semiconductor",
        "chip",
        "foundry",
        "gpu",
        "fab",
        "wafer",
        "lithography",
    ],
    "shipping": [
        "shipping",
        "logistics",
        "freight",
        "route",
        "supply chain",
        "port",
        "container",
        "suez",
        "panama canal",
    ],
    "tariff": [
        "tariff",
        "trade war",
        "import duty",
        "customs",
        "protectionism",
        "trade barrier",
    ],
    "inflation": [
        "inflation",
        "cpi",
        "price pressure",
        "cost of living",
        "hyperinflation",
    ],
    "interest_rate": [
        "interest rate",
        "fed",
        "rate cut",
        "rate hike",
        "monetary policy",
        "central bank",
        "fomc",
    ],
    "climate": [
        "climate",
        "hurricane",
        "flood",
        "drought",
        "wildfire",
        "emission",
        "carbon",
        "esg",
    ],
    "regulation": [
        "regulation",
        "regulatory",
        "antitrust",
        "legislation",
        "compliance",
        "data privacy",
        "gdpr",
    ],
    "cyber": [
        "cyber",
        "hack",
        "breach",
        "ransomware",
        "cybersecurity",
    ],
    "middle_east": [
        "iran",
        "israel",
        "saudi",
        "middle east",
        "gulf",
        "houthi",
        "hezbollah",
    ],
    "russia_ukraine": [
        "russia",
        "ukraine",
        "nato",
        "kremlin",
        "moscow",
    ],
}


def extract_themes(event: EventInput) -> list[str]:
    """Extract risk themes from event text using keyword matching.

    Scans the event's title, description, and tags for keywords
    associated with each theme.

    Returns a deduplicated list of matched theme names.
    """
    text = " ".join(
        [event.title, event.description, " ".join(event.tags)]
    ).lower()

    matched = [
        theme
        for theme, keywords in THEME_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    return matched
