"""Generate synthetic OHLCV CSV fixtures for 3 market scenarios.

Run: python tests/fixtures/generate.py
Outputs: ohlcv_bullish.csv, ohlcv_bearish.csv, ohlcv_sideways.csv
Each: 200 rows, columns = date, open, high, low, close, volume.
Prices in thousands VND (matching vnstock KBS convention).
"""
import os
from datetime import date, timedelta
import pandas as pd
import numpy as np


def _business_days(n: int, start: str = "2025-09-01") -> list:
    d = date.fromisoformat(start)
    days = []
    while len(days) < n:
        if d.weekday() < 5:  # Mon–Fri
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def _ohlcv_from_close(dates, closes, vol_base=2_000_000, vol_noise=500_000, seed=42):
    rng = np.random.default_rng(seed)
    opens = closes * (1 + rng.normal(0, 0.003, len(closes)))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.005, len(closes))))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.005, len(closes))))
    vols = (vol_base + rng.normal(0, vol_noise, len(closes))).clip(min=100_000).astype(int)
    return pd.DataFrame({
        "date": dates, "open": opens.round(2), "high": highs.round(2),
        "low": lows.round(2), "close": closes.round(2), "volume": vols,
    })


def build_bullish(n=200, start_price=50.0, end_price=80.0, seed=1):
    rng = np.random.default_rng(seed)
    trend = np.linspace(start_price, end_price, n)
    noise = rng.normal(0, 0.6, n)
    closes = trend + noise
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def build_bearish(n=200, start_price=80.0, end_price=50.0, seed=2):
    rng = np.random.default_rng(seed)
    trend = np.linspace(start_price, end_price, n)
    noise = rng.normal(0, 0.6, n)
    closes = trend + noise
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def build_sideways(n=200, center=60.0, amplitude=2.0, seed=3):
    rng = np.random.default_rng(seed)
    closes = center + amplitude * np.sin(np.linspace(0, 6 * np.pi, n)) + rng.normal(0, 0.5, n)
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def main():
    out_dir = os.path.dirname(__file__)
    build_bullish().to_csv(os.path.join(out_dir, "ohlcv_bullish.csv"), index=False)
    build_bearish().to_csv(os.path.join(out_dir, "ohlcv_bearish.csv"), index=False)
    build_sideways().to_csv(os.path.join(out_dir, "ohlcv_sideways.csv"), index=False)
    print("Generated 3 fixtures.")


if __name__ == "__main__":
    main()
