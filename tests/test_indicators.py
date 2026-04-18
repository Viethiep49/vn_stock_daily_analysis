"""Unit tests for IndicatorEngine."""
import os
import pytest
import pandas as pd
from src.scoring.indicators import IndicatorEngine, IndicatorSet, InsufficientDataError


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def bullish_df():
    return pd.read_csv(os.path.join(FIXTURE_DIR, "ohlcv_bullish.csv"))


@pytest.fixture
def engine():
    return IndicatorEngine()


class TestIndicatorEngine:
    def test_returns_indicator_set(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert isinstance(out, IndicatorSet)

    def test_ma_computed_and_prev_available(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.MA20 is not None
        assert out.prev_MA20 is not None
        assert out.MA50 is not None

    def test_bullish_ma20_above_ma50(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.MA20 > out.MA50, "bullish scenario: MA20 should be above MA50"

    def test_rsi_in_valid_range(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert 0 <= out.RSI14 <= 100

    def test_bollinger_order(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.BB_lower < out.BB_mid < out.BB_upper

    def test_volume_ratio_positive(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.volume_ratio > 0

    def test_support_below_resistance(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.support_20 < out.resistance_20

    def test_insufficient_data_raises(self, engine):
        short_df = pd.DataFrame({
            "date": ["2026-01-01", "2026-01-02"],
            "open": [10, 10], "high": [11, 11],
            "low": [9, 9], "close": [10, 10], "volume": [1000, 1000],
        })
        with pytest.raises(InsufficientDataError):
            engine.compute(short_df)

    def test_bearish_ma20_below_ma50(self, engine):
        df = pd.read_csv(os.path.join(FIXTURE_DIR, "ohlcv_bearish.csv"))
        out = IndicatorEngine().compute(df)
        assert out.MA20 < out.MA50, "bearish scenario: MA20 should be below MA50"
