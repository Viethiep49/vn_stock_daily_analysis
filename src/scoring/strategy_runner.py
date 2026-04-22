"""YAML-driven strategy definition + safe rule evaluation."""
import os
import glob
import yaml
from typing import List, Optional
from dataclasses import asdict, is_dataclass
from pydantic import BaseModel, Field, field_validator, model_validator
from asteval import Interpreter
from src.scoring.signals import Signal
from src.scoring.aggregator import ScoreCard


class RuleConfig(BaseModel):
    when: Optional[str] = None
    default: bool = False
    score: int = Field(ge=0, le=100)
    signal: Signal
    reason: str

    @model_validator(mode="after")
    def _xor_when_default(self):
        if self.default and self.when:
            raise ValueError("Rule cannot have both `default` and `when`")
        if not self.default and not self.when:
            raise ValueError("Rule must have either `when` or `default: true`")
        return self


class StrategyConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    weight: float = Field(gt=0)
    enabled: bool = True
    indicators_required: List[str] = Field(default_factory=list)
    rules: List[RuleConfig] = Field(min_length=1)

    @field_validator("rules")
    @classmethod
    def _validate_rules(cls, rules: List[RuleConfig]) -> List[RuleConfig]:
        defaults = [i for i, r in enumerate(rules) if r.default]
        if len(defaults) != 1:
            raise ValueError(
                f"Exactly one rule must have `default: true`, got {len(defaults)}"
            )
        if defaults[0] != len(rules) - 1:
            raise ValueError("Default rule must be the LAST rule")
        return rules




class RuleEvaluator:
    """Evaluate a boolean rule expression against a variable context.

    - Uses asteval (restricted AST). No imports, no builtins like open().
    - Missing or None variables cause the expression to return False (skip rule).
    - Any syntax error or attempt to access a dangerous name raises ValueError.
    """

    # asteval's default interpreter already strips __import__, exec, eval,
    # open, and similar. We still guard by checking the source text.
    _BLOCKED_TOKENS = ("__", "import", "open(", "exec(", "eval(", "compile(")

    def eval(self, expr: str, context: dict) -> bool:
        for tok in self._BLOCKED_TOKENS:
            if tok in expr:
                raise ValueError(f"Expression contains blocked token: {tok!r}")

        interp = Interpreter(no_print=True)
        # Reject None-valued or missing variables by short-circuiting to False
        safe_ctx = {k: v for k, v in context.items() if v is not None}
        for k, v in safe_ctx.items():
            interp.symtable[k] = v

        try:
            result = interp(expr)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr!r}: {e}")

        if interp.error:
            # asteval accumulates errors in .error; a NameError for missing
            # variables should yield False (skip), not raise.
            first = interp.error[0]
            msg = str(first.get_error())
            if "not defined" in msg or "NameError" in msg:
                return False
            raise ValueError(f"Eval error for {expr!r}: {msg}")

        return bool(result)


class StrategyRunner:
    def __init__(self, strategies: List[StrategyConfig]):
        self.strategies = strategies
        self.evaluator = RuleEvaluator()

    @classmethod
    def load_dir(cls, directory: str) -> "StrategyRunner":
        """Load *.yaml from directory, validate, return runner."""
        paths = sorted(glob.glob(os.path.join(directory, "*.yaml")))
        strategies: List[StrategyConfig] = []
        for p in paths:
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            strategies.append(StrategyConfig(**data))
        return cls(strategies)

    def run(self, context) -> List[ScoreCard]:
        """Evaluate all enabled strategies against the indicator context.

        `context` may be an IndicatorSet dataclass or a plain dict.
        """
        ctx = _as_dict(context)
        cards: List[ScoreCard] = []
        for cfg in self.strategies:
            if not cfg.enabled:
                continue
            if any(ctx.get(i) is None for i in cfg.indicators_required):
                continue
            card = self._evaluate_one(cfg, ctx)
            if card is not None:
                cards.append(card)
        return cards

    def _evaluate_one(self, cfg: StrategyConfig, ctx: dict) -> Optional[ScoreCard]:
        for idx, rule in enumerate(cfg.rules):
            if rule.default:
                matched = True
            else:
                matched = self.evaluator.eval(rule.when, ctx)
            if matched:
                return ScoreCard(
                    strategy_name=cfg.name,
                    score=rule.score,
                    signal=rule.signal,
                    reason=rule.reason,
                    weight=cfg.weight,
                    rule_matched=idx,
                )
        return None  # unreachable if default rule present


def _as_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Unsupported context type: {type(obj)}")
