# Risk Engine — Developer Guide

This is your sandbox. Everything in `backend/app/risk_engine/` is **pure Python** — no web framework, no database, no async. You can edit any file here without worrying about breaking the rest of the app.

## Quick Start

```bash
cd backend

# Run your code directly
python -c "
from app.risk_engine import EventInput, CompanyInput, match_event_to_companies

event = EventInput(
    title='China escalates military pressure on Taiwan',
    description='Escalation risk stresses semiconductor supply chains',
    category='geopolitical',
    tags=['taiwan', 'china', 'semiconductor'],
    probability=0.28,
)
company = CompanyInput(
    company_id='nvda',
    ticker='NVDA',
    sector='Semiconductors',
    exposures={'Taiwan / foundry': 9, 'China demand': 7, 'Export controls': 8},
)
matches = match_event_to_companies(event, [company])
for cid, m in matches:
    print(f'{cid}: score={m.relevance_score}, themes={m.matched_themes}')
"

# Run tests
pytest tests/test_risk_engine/ -v
```

---

## File Map

```
risk_engine/
├── types.py            ← Data classes (inputs and outputs)
├── themes.py           ← Keyword dictionaries + theme extraction
├── matcher.py          ← Event↔company scoring logic
├── scoring.py          ← Relevance formula + aggregate risk score
├── sector_defaults.py  ← Default risk profiles by sector
└── __init__.py         ← Public API (re-exports everything)
```

### What each file does

**`types.py`** — The contract between the engine and the rest of the system. Four dataclasses:

| Type | Purpose |
|------|---------|
| `EventInput` | What an event looks like to the engine: title, description, category, tags, probability |
| `CompanyInput` | What a company looks like: id, ticker, sector, and an `exposures` dict mapping labels to 0-10 weights |
| `ExposureMatch` | Output of matching one event to one company: relevance_score (0-100), matched_themes, explanation |
| `CompanyRiskResult` | Output of aggregating all event matches for one company: risk_score, avg, peak, count |

**`themes.py`** — Maps event text to risk themes via keyword matching. The `THEME_KEYWORDS` dict is the core configuration. Each key is a theme name, each value is a list of keywords to search for in the event's title + description + tags.

**`matcher.py`** — The main scoring logic. `score_event_for_company()` extracts themes from an event, finds overlapping exposure labels in the company's profile, and combines everything into a relevance score.

**`scoring.py`** — The math. `event_relevance_score()` is the per-event formula. `aggregate_risk_score()` rolls per-event scores into a company-level number.

**`sector_defaults.py`** — Preset `exposures` dicts for common sectors (Semiconductors, Energy, Finance, etc.). Applied when a user creates a company if they don't provide their own.

---

## How Things Flow

```
Event text → extract_themes() → list of theme names
                                       ↓
Company exposures dict ────────→ score_event_for_company()
                                       ↓
                                 ExposureMatch (score, themes, explanation)
                                       ↓
              collect all matches → compute_company_risk()
                                       ↓
                                 CompanyRiskResult (aggregate score)
```

The rest of the app (database, API, frontend) calls these functions and handles persistence. You never need to touch that layer.

---

## What You Can Change

### 1. Add or modify themes (`themes.py`)

Add a new geopolitical risk category:

```python
THEME_KEYWORDS["ai_regulation"] = [
    "ai regulation",
    "artificial intelligence",
    "foundation model",
    "eu ai act",
    "compute governance",
]
```

That's it. Events mentioning these keywords will now match companies with relevant exposure labels.

### 2. Tune the scoring formula (`scoring.py`)

Current formula in `event_relevance_score()`:

```
score = probability × (0.45 + 0.45 × exposure_weight/10 + 0.10 × keyword_hits/4) × 100
```

The three components:
- **Probability (45%)** — how likely is the event?
- **Exposure weight (45%)** — how exposed is the company (0-10 scale)?
- **Keyword hits (10%)** — how many keyword matches in the exposure labels?

To emphasize probability more:
```python
score = prob_component * (0.60 + 0.30 * exposure_component + 0.10 * hit_boost)
```

To add a volatility term:
```python
def event_relevance_score(probability, exposure_weight, keyword_hits=1, volatility=0.0):
    # ... existing components ...
    vol_boost = min(1.0, volatility / 0.5)  # normalize to 0-1
    score = prob_component * (0.35 + 0.35 * exposure_component + 0.10 * hit_boost + 0.20 * vol_boost)
```

If you add new parameters to this function, also update `matcher.py` where it's called.

### 3. Change the aggregation model (`scoring.py`)

Current model in `aggregate_risk_score()`:

```
company_risk = 0.7 × avg(event_scores) + 0.3 × max(event_scores)
```

The 70/30 blend means average risk matters most, but a single extreme event can't be fully averaged away.

Ideas for v2:
- **Correlation-adjusted**: discount overlapping themes (two oil events shouldn't double-count)
- **Concentration penalty**: flag companies where >50% of risk comes from one theme
- **Value-at-Risk**: compute a VaR-like "X% of scenarios result in score > Y"
- **Monte Carlo**: simulate event outcomes using probability distributions

Example — add correlation discounting:

```python
def aggregate_risk_score(relevance_scores: list[int], themes_per_event: list[list[str]] | None = None) -> int:
    if not relevance_scores:
        return 0

    # Discount events that share themes (correlated risks)
    if themes_per_event and len(themes_per_event) == len(relevance_scores):
        adjusted = []
        seen_themes: set[str] = set()
        for score, themes in sorted(zip(relevance_scores, themes_per_event), reverse=True):
            overlap = len(set(themes) & seen_themes) / max(1, len(themes))
            discount = 1.0 - 0.5 * overlap  # 50% discount for fully overlapping themes
            adjusted.append(int(score * discount))
            seen_themes.update(themes)
        relevance_scores = adjusted

    avg_score = sum(relevance_scores) / len(relevance_scores)
    peak_score = max(relevance_scores)
    return int(round(0.7 * avg_score + 0.3 * peak_score))
```

### 4. Add or tune sector defaults (`sector_defaults.py`)

Each sector has a dict of `{exposure_label: weight}` where weight is 0-10:

```python
SECTOR_DEFAULTS["Aerospace"] = {
    "Geopolitical conflict": 8,
    "Export controls": 9,
    "Government spending": 8,
    "Supply chain disruption": 6,
    "FX": 4,
    "Tariffs": 5,
}
```

The label strings are matched against theme keywords in `matcher.py`. Use labels that contain keywords from `themes.py` for best matching. For example, "Taiwan / foundry" matches the `taiwan_china_conflict` theme because "taiwan" appears in the label.

### 5. Improve the matching logic (`matcher.py`)

Current matching in `score_event_for_company()`:
1. Extract themes from event text
2. For each theme, find the company exposure label that has the most keyword overlap
3. Use that label's weight in the score formula
4. If no label matches a theme directly, use 60% of the company's average weight (soft match)

Ideas for improvement:
- **TF-IDF or embedding similarity** instead of keyword matching
- **Sector-specific theme weights** (oil_shock matters more for Energy than Tech)
- **Time decay** (events closer to resolution date should score higher)
- **LLM-based classification** for edge cases the keyword dict misses

---

## The Contract

The rest of the system depends on these function signatures:

```python
# themes.py
def extract_themes(event: EventInput) -> list[str]

# matcher.py
def score_event_for_company(event: EventInput, company: CompanyInput) -> ExposureMatch
def match_event_to_companies(event: EventInput, companies: list[CompanyInput], min_score: int = 20) -> list[tuple[str, ExposureMatch]]

# scoring.py
def event_relevance_score(probability: float, exposure_weight: float, keyword_hits: int = 1) -> int
def aggregate_risk_score(relevance_scores: list[int]) -> int
def compute_company_risk(company_id: str, matches: list[ExposureMatch]) -> CompanyRiskResult

# sector_defaults.py
def get_default_risk_profile(sector: str) -> dict[str, int]
```

As long as these functions accept the same inputs and return the same types, you can change anything inside them. Add parameters with defaults if you need new inputs — the existing callers will keep working.

---

## Testing

Create test files in `tests/test_risk_engine/`. No database or fixtures needed:

```python
# tests/test_risk_engine/test_matcher.py
from app.risk_engine import EventInput, CompanyInput, score_event_for_company

def test_taiwan_event_matches_semiconductor_company():
    event = EventInput(
        title="China invades Taiwan",
        description="Military escalation disrupts TSMC production",
        category="conflict",
        tags=["taiwan", "china", "semiconductor"],
        probability=0.15,
    )
    company = CompanyInput(
        company_id="nvda",
        ticker="NVDA",
        sector="Semiconductors",
        exposures={"Taiwan / foundry": 9, "China demand": 7},
    )
    match = score_event_for_company(event, company)
    assert match.relevance_score > 0
    assert "taiwan_china_conflict" in match.matched_themes

def test_unrelated_event_scores_zero():
    event = EventInput(
        title="New York City mayoral election",
        description="Local election with no geopolitical implications",
        category="politics",
        tags=["election", "nyc"],
        probability=0.5,
    )
    company = CompanyInput(
        company_id="xom",
        ticker="XOM",
        sector="Energy",
        exposures={"Oil price": 9, "Middle East": 8},
    )
    match = score_event_for_company(event, company)
    assert match.relevance_score == 0

def test_high_probability_increases_score():
    event_low = EventInput("Taiwan", "", "conflict", ["taiwan"], probability=0.1)
    event_high = EventInput("Taiwan", "", "conflict", ["taiwan"], probability=0.8)
    company = CompanyInput("c1", "TSM", "Semiconductors", {"Taiwan / foundry": 9})

    low = score_event_for_company(event_low, company)
    high = score_event_for_company(event_high, company)
    assert high.relevance_score > low.relevance_score
```

Run: `cd backend && pytest tests/test_risk_engine/ -v`

---

## Data Available to You

When the system calls your engine, it provides:

**Per event:**
- `title` — event headline (up to 500 chars)
- `description` — longer description (up to 2000 chars)
- `category` — one of: geopolitical, trade, regulatory, climate, conflict, economic
- `tags` — empty list currently (future: extracted from source)
- `probability` — 0.0 to 1.0, from prediction markets (Polymarket, Kalshi, Metaculus)

**Per company:**
- `company_id` — UUID string
- `ticker` — stock ticker (e.g. "NVDA")
- `sector` — sector string (e.g. "Semiconductors")
- `exposures` — the risk profile dict, e.g. `{"Taiwan / foundry": 9, "China demand": 7}`

The integration layer (`services/risk_service.py`) also has access to company financials (annual_revenue, operating_expense, capital_expense) from the database. If you want financial data passed into the engine, add fields to `CompanyInput` in `types.py` and ask Yajvan to update the mapper in `risk_service.py`.

---

## Future Directions

Some ideas for where to take this:

1. **NLP-based theme extraction** — replace keyword matching with sentence embeddings or an LLM classifier for better coverage
2. **Financial factor models** — incorporate revenue concentration, supply chain dependency graphs, FX exposure
3. **Cross-event correlation** — model how events interact (e.g. Taiwan conflict + oil shock compound each other)
4. **Historical backtesting** — use probability history data to validate scoring accuracy
5. **Monte Carlo simulation** — simulate portfolio outcomes across probability distributions
6. **Regime detection** — identify when the risk environment shifts (e.g. "elevated geopolitical risk regime")
7. **Dynamic exposure weights** — infer company exposures from earnings transcripts, supply chain data, or news

All of these can be implemented inside `risk_engine/` without changing the integration layer, as long as you keep the function signatures stable.
