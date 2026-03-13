"""Theme-based hedge instrument catalog.

Maps geopolitical themes to suggested hedge instruments (ETFs, options,
futures, bonds).  Andre can tune these recommendations based on market
conditions and research.
"""

from dataclasses import dataclass


@dataclass
class HedgeInstrument:
    ticker: str
    instrument_type: str  # ETF, Options, Futures, Bond
    direction: str        # long, short
    rationale: str


THEME_HEDGE_MAP: dict[str, list[HedgeInstrument]] = {
    "taiwan_china_conflict": [
        HedgeInstrument("ITA", "ETF", "short", "Defense sector exposure to Taiwan conflict"),
        HedgeInstrument("XLE", "ETF", "long", "Energy spike hedge"),
        HedgeInstrument("TLT", "ETF", "long", "Flight-to-safety bond play"),
        HedgeInstrument("VIX calls", "Options", "long", "Volatility hedge"),
    ],
    "export_controls": [
        HedgeInstrument("SOXX puts", "Options", "long", "Semiconductor sector downside"),
        HedgeInstrument("SMH puts", "Options", "long", "Semiconductor ETF hedge"),
    ],
    "recession": [
        HedgeInstrument("TLT", "ETF", "long", "Treasury flight to safety"),
        HedgeInstrument("GLD", "ETF", "long", "Gold inflation/recession hedge"),
        HedgeInstrument("VIX calls", "Options", "long", "Volatility spike hedge"),
        HedgeInstrument("XLP", "ETF", "long", "Consumer staples defensive play"),
    ],
    "oil_shock": [
        HedgeInstrument("XLE", "ETF", "long", "Energy sector upside capture"),
        HedgeInstrument("WTI futures", "Futures", "long", "Direct oil exposure"),
        HedgeInstrument("USO", "ETF", "long", "Oil ETF proxy"),
    ],
    "semiconductor": [
        HedgeInstrument("SOXX puts", "Options", "long", "Semiconductor index downside"),
        HedgeInstrument("SMH puts", "Options", "long", "Semiconductor ETF hedge"),
        HedgeInstrument("TSM puts", "Options", "long", "TSMC direct hedge"),
    ],
    "shipping": [
        HedgeInstrument("BDRY", "ETF", "long", "Dry bulk shipping rates"),
        HedgeInstrument("XLE", "ETF", "long", "Energy cost hedge"),
    ],
    "tariff": [
        HedgeInstrument("EEM puts", "Options", "long", "Emerging markets downside"),
        HedgeInstrument("UUP", "ETF", "long", "Dollar strength play"),
        HedgeInstrument("GLD", "ETF", "long", "Safe haven hedge"),
    ],
    "inflation": [
        HedgeInstrument("TIP", "ETF", "long", "TIPS inflation protection"),
        HedgeInstrument("GLD", "ETF", "long", "Gold inflation hedge"),
        HedgeInstrument("DBC", "ETF", "long", "Broad commodity exposure"),
    ],
    "interest_rate": [
        HedgeInstrument("TLT puts", "Options", "long", "Long bond downside on rate hike"),
        HedgeInstrument("SHY", "ETF", "long", "Short-term treasury safety"),
        HedgeInstrument("XLF", "ETF", "short", "Financials sector hedge"),
    ],
    "climate": [
        HedgeInstrument("XLE", "ETF", "short", "Fossil fuel transition risk"),
        HedgeInstrument("ICLN", "ETF", "long", "Clean energy upside"),
        HedgeInstrument("Cat bonds", "Bond", "long", "Catastrophe bond protection"),
    ],
    "regulation": [
        HedgeInstrument("XLF puts", "Options", "long", "Financial sector reg risk"),
        HedgeInstrument("XLV puts", "Options", "long", "Healthcare reg risk"),
    ],
    "cyber": [
        HedgeInstrument("CIBR", "ETF", "long", "Cybersecurity sector upside"),
        HedgeInstrument("BUG", "ETF", "long", "Cybersecurity ETF"),
        HedgeInstrument("VIX calls", "Options", "long", "Volatility spike hedge"),
    ],
    "middle_east": [
        HedgeInstrument("XLE", "ETF", "long", "Energy spike on conflict"),
        HedgeInstrument("GLD", "ETF", "long", "Safe haven hedge"),
        HedgeInstrument("TLT", "ETF", "long", "Flight to safety"),
        HedgeInstrument("WTI futures", "Futures", "long", "Direct oil exposure"),
    ],
    "russia_ukraine": [
        HedgeInstrument("XLE", "ETF", "long", "European energy crisis hedge"),
        HedgeInstrument("WEAT", "ETF", "long", "Wheat supply disruption"),
        HedgeInstrument("GLD", "ETF", "long", "Safe haven hedge"),
        HedgeInstrument("TLT", "ETF", "long", "Flight to safety"),
    ],
}


def get_hedge_instruments(themes: list[str]) -> list[HedgeInstrument]:
    """Return deduplicated hedge instruments for given themes.

    Deduplication is by ticker — if multiple themes suggest the same
    ticker, the first occurrence wins.
    """
    seen: set[str] = set()
    result: list[HedgeInstrument] = []

    for theme in themes:
        instruments = THEME_HEDGE_MAP.get(theme, [])
        for inst in instruments:
            if inst.ticker not in seen:
                seen.add(inst.ticker)
                result.append(inst)

    return result
