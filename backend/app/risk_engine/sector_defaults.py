"""Default risk profiles by sector.

These are applied when a company is created if the user doesn't
provide a custom risk profile. Users can override them later.

Each profile maps exposure labels to weights (0-10 scale):
  0 = no exposure, 10 = maximum exposure

To add a new sector or adjust weights, edit SECTOR_DEFAULTS below.
"""

SECTOR_DEFAULTS: dict[str, dict[str, int]] = {
    "Semiconductors": {
        "Taiwan / foundry": 9,
        "China demand": 7,
        "Export controls": 8,
        "Energy / power": 4,
        "Shipping": 5,
        "Semiconductor cycle": 9,
        "Tariffs": 6,
    },
    "Consumer Electronics": {
        "China manufacturing": 10,
        "Taiwan / chips": 7,
        "Consumer demand": 8,
        "FX": 6,
        "Shipping": 5,
        "Recession sensitivity": 7,
        "Tariffs": 8,
    },
    "Energy": {
        "Oil price": 9,
        "Middle East": 8,
        "Shipping": 7,
        "Climate regulation": 6,
        "Russia / sanctions": 7,
        "Recession sensitivity": 5,
        "OPEC policy": 8,
    },
    "Finance": {
        "Recession sensitivity": 8,
        "Interest rates": 9,
        "FX": 7,
        "Regulation": 6,
        "Cyber risk": 5,
        "Inflation": 7,
    },
    "Automotive": {
        "China manufacturing": 7,
        "Tariffs": 8,
        "Semiconductor supply": 7,
        "Consumer demand": 7,
        "FX": 5,
        "Climate regulation": 6,
        "Shipping": 5,
    },
    "Pharmaceuticals": {
        "China supply chain": 6,
        "Regulation": 8,
        "FX": 5,
        "Recession sensitivity": 3,
        "Shipping": 4,
        "Tariffs": 4,
    },
    "Defense": {
        "Geopolitical conflict": 9,
        "Government spending": 8,
        "Export controls": 7,
        "Taiwan / China": 6,
        "Russia / Ukraine": 7,
        "Middle East": 7,
    },
    "Agriculture": {
        "Climate events": 9,
        "Shipping": 7,
        "FX": 5,
        "Tariffs": 7,
        "Russia / Ukraine": 6,
        "Inflation": 5,
    },
    "Technology": {
        "Regulation": 7,
        "China demand": 6,
        "Export controls": 6,
        "Cyber risk": 7,
        "Recession sensitivity": 5,
        "FX": 5,
        "Tariffs": 5,
    },
    "Mining": {
        "Commodity prices": 9,
        "China demand": 8,
        "Climate regulation": 6,
        "Shipping": 6,
        "Geopolitical risk": 5,
        "FX": 5,
    },
}


def get_default_risk_profile(sector: str) -> dict[str, int]:
    """Return the default risk profile for a sector.

    Tries exact match first, then case-insensitive substring match.
    Returns an empty dict if no match is found.
    """
    if sector in SECTOR_DEFAULTS:
        return dict(SECTOR_DEFAULTS[sector])

    sector_lower = sector.lower()
    for key, profile in SECTOR_DEFAULTS.items():
        if key.lower() in sector_lower or sector_lower in key.lower():
            return dict(profile)

    return dict(_GENERAL_FALLBACK)


_GENERAL_FALLBACK: dict[str, int] = {
    "Geopolitical risk": 5,
    "Recession sensitivity": 5,
    "Tariffs": 5,
    "FX": 4,
    "Regulation": 5,
    "Shipping": 3,
    "China demand": 4,
}
