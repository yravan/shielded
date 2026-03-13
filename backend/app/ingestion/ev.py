"""Event classification helpers.

Simplified: binary (1 market) or qualitative (2+ markets).
The "quantitative" classification has been removed — forecast_percentile_history
returns 400 for all numeric-strike events with mutually_exclusive=False.
"""
