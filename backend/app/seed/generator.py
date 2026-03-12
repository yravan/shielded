"""Bounded random walk generator for realistic probability histories.

Uses an Ornstein-Uhlenbeck-like mean-reverting process to generate
realistic probability time series data.
"""

import random
from datetime import datetime, timedelta, timezone


def generate_probability_history(
    event_id: str,
    base_prob: float,
    volatility: float = 0.03,
    days: int = 90,
    points_per_day: int = 24,
) -> list[dict]:
    """Generate realistic probability history using a mean-reverting random walk.

    Args:
        event_id: UUID string of the event.
        base_prob: The mean probability to revert toward.
        volatility: Standard deviation of random perturbations.
        days: Number of days of history to generate.
        points_per_day: Number of data points per day.

    Returns:
        List of dicts compatible with ProbabilityHistory model.
    """
    random.seed(hash(event_id) % (2**31))

    theta = 0.1  # mean reversion speed
    dt = 1.0 / points_per_day
    current = base_prob
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    history = []
    total_points = days * points_per_day

    for i in range(total_points):
        timestamp = start + timedelta(hours=i * (24.0 / points_per_day))

        # Ornstein-Uhlenbeck process: dp = theta * (mu - x) * dt + sigma * dW
        dp = theta * (base_prob - current) * dt + volatility * random.gauss(0, 1) * (dt**0.5)
        current += dp

        # Clamp to valid probability range
        current = max(0.01, min(0.99, current))

        # Generate plausible bid/ask spread
        spread = random.uniform(0.01, 0.04)
        bid = max(0.01, current - spread / 2)
        ask = min(0.99, current + spread / 2)

        # Generate plausible volume (higher near current time)
        time_factor = (i + 1) / total_points
        base_volume = random.uniform(50000, 500000)
        volume = base_volume * (0.5 + 0.5 * time_factor)

        history.append(
            {
                "event_id": event_id,
                "probability": round(current, 4),
                "source_bid": round(bid, 4),
                "source_ask": round(ask, 4),
                "volume_24h": round(volume, 2),
                "recorded_at": timestamp,
            }
        )

    return history
