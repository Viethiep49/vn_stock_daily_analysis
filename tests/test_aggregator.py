"""Unit tests for ScoreCard, AnalysisReport, ScoreAggregator."""
import pytest
from src.scoring.signals import Signal
from src.scoring.aggregator import ScoreCard, AnalysisReport, ScoreAggregator


def card(name, score, weight=1.0, signal=Signal.NEUTRAL, reason="r", rule_matched=0):
    return ScoreCard(
        strategy_name=name, score=score, signal=signal,
        reason=reason, weight=weight, rule_matched=rule_matched,
    )


class TestScoreAggregator:
    def setup_method(self):
        self.agg = ScoreAggregator()

    def test_empty_cards_raises(self):
        with pytest.raises(ValueError):
            self.agg.aggregate([])

    def test_single_card_composite_equals_score(self):
        r = self.agg.aggregate([card("A", 72, weight=1.0)])
        assert r.composite == 72
        assert r.final_signal is Signal.BUY

    def test_equal_weights_is_mean(self):
        cards = [card("A", 80, 1.0), card("B", 60, 1.0), card("C", 40, 1.0)]
        r = self.agg.aggregate(cards)
        assert r.composite == pytest.approx(60.0)
        assert r.final_signal is Signal.NEUTRAL

    def test_weighted_average(self):
        # 90*2 + 50*1 = 230; weights=3; composite ≈ 76.67 → BUY
        cards = [card("A", 90, 2.0), card("B", 50, 1.0)]
        r = self.agg.aggregate(cards)
        assert r.composite == pytest.approx(230 / 3)
        assert r.final_signal is Signal.BUY

    def test_zero_weight_is_rejected(self):
        with pytest.raises(ValueError):
            self.agg.aggregate([card("A", 50, weight=0.0)])

    def test_report_preserves_cards(self):
        cards = [card("A", 80), card("B", 40)]
        r = self.agg.aggregate(cards)
        assert len(r.cards) == 2
        assert r.cards[0].strategy_name == "A"

    def test_composite_clamped_to_int_0_100(self):
        r = self.agg.aggregate([card("A", 100)])
        assert 0 <= r.composite <= 100


class TestAnalysisReport:
    def test_has_optional_narrative(self):
        r = AnalysisReport(composite=70, final_signal=Signal.BUY, cards=[])
        assert r.narrative is None
        r.narrative = "LLM text"
        assert r.narrative == "LLM text"
