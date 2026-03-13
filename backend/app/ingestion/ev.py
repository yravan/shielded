"""Expected value computation for multi-market events."""

import re

from app.ingestion.base import NormalizedMarket


def extract_numeric_value(label: str) -> float | None:
    """Extract a numeric value from an outcome label.

    Handles patterns like:
      "Above 10", "10 or more", "10-15" (midpoint), "15.5", "$10M"
      Returns None for non-numeric labels like "Claude", "Biden", "Yes/No".
    """
    label = label.strip()

    # "Above X", "Over X", "More than X", "At least X", ">X", ">=X", "X or more", "X+"
    m = re.search(
        r"(?:above|over|more than|at least|>=?)\s*\$?([\d,]+\.?\d*)", label, re.IGNORECASE
    )
    if m:
        return float(m.group(1).replace(",", ""))

    m = re.search(r"([\d,]+\.?\d*)\s*(?:or more|\+)", label, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))

    # "Below X", "Under X", "Less than X", "<X", "<=X", "X or fewer"
    m = re.search(
        r"(?:below|under|less than|at most|<=?)\s*\$?([\d,]+\.?\d*)", label, re.IGNORECASE
    )
    if m:
        return float(m.group(1).replace(",", ""))

    m = re.search(r"([\d,]+\.?\d*)\s*(?:or fewer|or less)", label, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", ""))

    # Range: "10-15", "10 to 15" → midpoint
    m = re.search(r"\$?([\d,]+\.?\d*)\s*[-–—]\s*\$?([\d,]+\.?\d*)", label)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", ""))
        return (lo + hi) / 2.0

    m = re.search(r"([\d,]+\.?\d*)\s+to\s+([\d,]+\.?\d*)", label, re.IGNORECASE)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", ""))
        return (lo + hi) / 2.0

    # Bare number: "15", "15.5", "$10"
    m = re.fullmatch(r"\$?([\d,]+\.?\d*)\s*[%MBKmbk]?", label.strip())
    if m:
        return float(m.group(1).replace(",", ""))

    return None


def is_quantitative_event(markets: list[NormalizedMarket]) -> bool:
    """True if mutually exclusive and >=50% of markets parse to numeric values."""
    if len(markets) < 2:
        return False

    numeric_count = sum(1 for m in markets if m.outcome_value is not None)
    return numeric_count / len(markets) >= 0.5


def compute_expected_value(markets: list[NormalizedMarket]) -> float | None:
    """Compute probability-weighted expected value: sum(p_i * v_i) / sum(p_i).

    Only uses markets with a parsed numeric outcome_value.
    Returns None if no numeric markets found.
    """
    numerator = 0.0
    denominator = 0.0

    for m in markets:
        if m.outcome_value is not None:
            numerator += m.probability * m.outcome_value
            denominator += m.probability

    if denominator <= 0:
        return None

    return round(numerator / denominator, 4)
