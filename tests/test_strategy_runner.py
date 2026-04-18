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
