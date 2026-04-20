"""Aggregation of per-strategy ScoreCards into a composite AnalysisReport."""
from dataclasses import dataclass, field
from typing import List, Optional
from src.scoring.signals import Signal, composite_to_signal


@dataclass
class ScoreCard:
    strategy_name: str
    score: int
    signal: Signal
    reason: str
    weight: float
    rule_matched: int


@dataclass
class AnalysisReport:
    composite: float
    final_signal: Signal
    cards: List[ScoreCard] = field(default_factory=list)
    narrative: Optional[str] = None
    # Optional data carried through for notifier/main.py rendering
    symbol: Optional[str] = None
    info: Optional[dict] = None
    quote: Optional[dict] = None
    circuit_breaker: Optional[dict] = None
    risk: Optional["RiskMetrics"] = None
    macro: Optional["MacroSnapshot"] = None
    valuation: Optional["ValuationResult"] = None


class ScoreAggregator:
    def aggregate(self, cards: List[ScoreCard]) -> AnalysisReport:
        if not cards:
            raise ValueError("Cannot aggregate empty cards list")
        total_weight = sum(c.weight for c in cards)
        if total_weight <= 0:
            raise ValueError("Total weight must be > 0")
        composite = sum(c.score * c.weight for c in cards) / total_weight
        composite = max(0.0, min(100.0, composite))
        return AnalysisReport(
            composite=composite,
            final_signal=composite_to_signal(composite),
            cards=list(cards),
        )
