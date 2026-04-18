"""Unit tests for Signal enum + composite_to_signal bucket."""
import pytest
from src.scoring.signals import Signal, composite_to_signal


class TestSignalEnum:
    def test_has_all_granular_values(self):
        expected = {
            "STRONG_BUY", "BUY", "BUY_WEAK",
            "NEUTRAL",
            "SELL_WEAK", "SELL", "STRONG_SELL",
        }
        assert {s.name for s in Signal} == expected

    def test_values_are_strings(self):
        assert Signal.BUY.value == "BUY"


class TestCompositeToSignal:
    @pytest.mark.parametrize("score,expected", [
        (0, Signal.STRONG_SELL),
        (19, Signal.STRONG_SELL),
        (20, Signal.SELL),
        (39, Signal.SELL),
        (40, Signal.NEUTRAL),
        (64, Signal.NEUTRAL),
        (65, Signal.BUY),
        (79, Signal.BUY),
        (80, Signal.STRONG_BUY),
        (100, Signal.STRONG_BUY),
    ])
    def test_boundaries(self, score, expected):
        assert composite_to_signal(score) is expected

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            composite_to_signal(-1)
        with pytest.raises(ValueError):
            composite_to_signal(101)

    def test_accepts_float(self):
        assert composite_to_signal(72.5) is Signal.BUY
