"""Unit tests for StrategyRunner schema, rule evaluator, and load_dir."""
import pytest
from pydantic import ValidationError
from src.scoring.strategy_runner import StrategyConfig


VALID_YAML = {
    "name": "MA Crossover",
    "weight": 1.0,
    "enabled": True,
    "indicators_required": ["MA20", "MA50"],
    "rules": [
        {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "uptrend"},
        {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fallback"},
    ],
}


class TestStrategyConfigSchema:
    def test_valid_config_loads(self):
        cfg = StrategyConfig(**VALID_YAML)
        assert cfg.name == "MA Crossover"
        assert cfg.weight == 1.0
        assert len(cfg.rules) == 2

    def test_name_required(self):
        bad = {**VALID_YAML}
        del bad["name"]
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_weight_must_be_positive(self):
        bad = {**VALID_YAML, "weight": 0}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_score_out_of_range_rejected(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 150, "signal": "BUY", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_rules_require_default_at_end(self):
        # Missing default rule
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_default_must_be_last_rule(self):
        bad = {**VALID_YAML, "rules": [
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_exactly_one_default(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb1"},
            {"default": True, "score": 50, "signal": "NEUTRAL", "reason": "fb2"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_invalid_signal_rejected(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BANANA", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)


from src.scoring.strategy_runner import RuleEvaluator


class TestRuleEvaluator:
    def setup_method(self):
        self.ev = RuleEvaluator()

    def test_simple_expression_true(self):
        assert self.ev.eval("a > b", {"a": 2, "b": 1}) is True

    def test_simple_expression_false(self):
        assert self.ev.eval("a > b", {"a": 1, "b": 2}) is False

    def test_compound_and(self):
        ctx = {"MA20": 10, "MA50": 8, "prev_MA20": 7, "prev_MA50": 8}
        assert self.ev.eval("MA20 > MA50 and prev_MA20 <= prev_MA50", ctx) is True

    def test_missing_variable_returns_false(self):
        # Rule referring to missing indicator -> skip (False)
        assert self.ev.eval("missing > 0", {"a": 1}) is False

    def test_none_value_returns_false(self):
        # If an indicator is None (NaN), comparisons skip
        assert self.ev.eval("x > 0", {"x": None}) is False

    def test_injection_import_blocked(self):
        with pytest.raises(ValueError):
            self.ev.eval("__import__('os').system('echo hi')", {})

    def test_injection_builtin_blocked(self):
        with pytest.raises(ValueError):
            self.ev.eval("open('/etc/passwd').read()", {})


from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreCard
from src.scoring.signals import Signal


def _make_indicator_ctx(**overrides):
    base = {
        "close": 60.0, "prev_close": 59.5,
        "MA5": 60.2, "MA10": 60.0, "MA20": 59.8, "MA50": 59.0, "MA200": None,
        "prev_MA5": 60.0, "prev_MA20": 59.9, "prev_MA50": 59.1,
        "RSI14": 58.0, "prev_RSI14": 55.0,
        "MACD": 0.2, "MACD_signal": 0.1, "MACD_hist": 0.1, "prev_MACD_hist": 0.05,
        "BB_upper": 62.0, "BB_mid": 60.0, "BB_lower": 58.0, "ATR14": 1.1,
        "volume": 2_000_000, "volume_ma20": 1_500_000, "volume_ratio": 1.33,
        "support_20": 58.5, "resistance_20": 61.5,
    }
    base.update(overrides)
    return base


class TestStrategyRunner:
    def test_loads_valid_strategy_from_dict(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        cards = runner.run(_make_indicator_ctx())
        assert len(cards) == 1
        assert isinstance(cards[0], ScoreCard)

    def test_matches_first_rule(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        # MA20 > MA50 -> should match first rule with score 65
        cards = runner.run(_make_indicator_ctx(MA20=60, MA50=55))
        assert cards[0].score == 65
        assert cards[0].signal is Signal.BUY
        assert cards[0].rule_matched == 0

    def test_falls_through_to_default(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        cards = runner.run(_make_indicator_ctx(MA20=55, MA50=60))
        assert cards[0].score == 40
        assert cards[0].signal is Signal.NEUTRAL
        assert cards[0].rule_matched == 1

    def test_disabled_strategy_skipped(self):
        cfg = StrategyConfig(**{**VALID_YAML, "enabled": False})
        runner = StrategyRunner([cfg])
        assert runner.run(_make_indicator_ctx()) == []

    def test_missing_required_indicator_skips(self):
        cfg = StrategyConfig(**{**VALID_YAML, "indicators_required": ["nonexistent"]})
        runner = StrategyRunner([cfg])
        assert runner.run(_make_indicator_ctx()) == []

    def test_load_dir_reads_yaml_files(self, tmp_path):
        yaml_content = """
name: "T1"
weight: 1.0
enabled: true
rules:
  - when: "close > 0"
    score: 70
    signal: BUY
    reason: "positive price"
  - default: true
    score: 40
    signal: NEUTRAL
    reason: "fallback"
"""
        (tmp_path / "t1.yaml").write_text(yaml_content, encoding="utf-8")
        runner = StrategyRunner.load_dir(str(tmp_path))
        assert len(runner.strategies) == 1
        cards = runner.run(_make_indicator_ctx())
        assert cards[0].score == 70
