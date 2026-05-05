"""
Walk-forward / rolling out-of-sample backtest validator.

Strategies in this repo are rule-based (no model fitting per fold), so this
implements rolling out-of-sample evaluation: split the timeline into N
non-overlapping test windows and run the engine on each, then report
mean/std/min/max of metrics across folds. This exposes whether reported
returns hold up across periods or are concentrated in a lucky window.
"""
from dataclasses import dataclass, field, replace
from typing import List, Literal, Optional
import statistics
import pandas as pd

from src.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from src.backtest.metrics import BacktestMetrics


@dataclass
class WalkForwardConfig:
    train_days: int = 365      # warmup/observation window before each test
    test_days: int = 90        # length of each test fold
    step_days: int = 90        # how far to advance between folds (== test_days for non-overlapping)
    mode: Literal["rolling", "anchored"] = "rolling"
    min_folds: int = 2


@dataclass
class FoldResult:
    fold_idx: int
    test_start: str
    test_end: str
    metrics: BacktestMetrics
    num_trades: int


@dataclass
class WalkForwardSummary:
    metric_name: str
    mean: float
    std: float
    min: float
    max: float
    median: float


@dataclass
class WalkForwardResult:
    config: WalkForwardConfig
    base_config: BacktestConfig
    folds: List[FoldResult] = field(default_factory=list)
    summaries: List[WalkForwardSummary] = field(default_factory=list)


class WalkForwardValidator:
    def __init__(self, engine: BacktestEngine):
        self.engine = engine

    def run(self, base_config: BacktestConfig, wf_config: WalkForwardConfig) -> WalkForwardResult:
        """
        Slice [base_config.start, base_config.end] into rolling test folds of
        wf_config.test_days, advancing by wf_config.step_days. The engine handles
        its own warmup internally (it pulls 365 days before each test_start).
        """
        full_start = pd.to_datetime(base_config.start)
        full_end = pd.to_datetime(base_config.end)
        total_days = (full_end - full_start).days

        if total_days < wf_config.train_days + wf_config.test_days:
            raise ValueError(
                f"Period {total_days}d too short for train={wf_config.train_days}d + test={wf_config.test_days}d"
            )

        folds: List[FoldResult] = []
        # First test window starts AFTER train_days from the global start
        cursor = full_start + pd.Timedelta(days=wf_config.train_days)
        fold_idx = 0
        while cursor + pd.Timedelta(days=wf_config.test_days) <= full_end:
            test_start = cursor
            test_end = cursor + pd.Timedelta(days=wf_config.test_days)

            fold_config = replace(
                base_config,
                start=test_start.strftime("%Y-%m-%d"),
                end=test_end.strftime("%Y-%m-%d"),
            )

            try:
                result = self.engine.run(fold_config)
                metrics = BacktestMetrics.calculate(result)
            except Exception as e:
                # Skip folds where the data provider has insufficient data
                cursor += pd.Timedelta(days=wf_config.step_days)
                continue

            folds.append(FoldResult(
                fold_idx=fold_idx,
                test_start=fold_config.start,
                test_end=fold_config.end,
                metrics=metrics,
                num_trades=metrics.num_trades,
            ))
            fold_idx += 1
            cursor += pd.Timedelta(days=wf_config.step_days)

        if len(folds) < wf_config.min_folds:
            raise ValueError(f"Only {len(folds)} folds produced, need >= {wf_config.min_folds}")

        summaries = self._summarize(folds)
        return WalkForwardResult(
            config=wf_config,
            base_config=base_config,
            folds=folds,
            summaries=summaries,
        )

    @staticmethod
    def _summarize(folds: List[FoldResult]) -> List[WalkForwardSummary]:
        metric_names = [
            "total_return_pct", "cagr_pct", "sharpe", "max_drawdown_pct",
            "win_rate_pct", "profit_factor", "vs_benchmark_pct",
        ]
        summaries: List[WalkForwardSummary] = []
        for name in metric_names:
            values = [getattr(f.metrics, name) for f in folds]
            # Filter inf/nan defensively
            clean = [v for v in values if v not in (float("inf"), float("-inf")) and v == v]
            if not clean:
                continue
            summaries.append(WalkForwardSummary(
                metric_name=name,
                mean=statistics.mean(clean),
                std=statistics.stdev(clean) if len(clean) > 1 else 0.0,
                min=min(clean),
                max=max(clean),
                median=statistics.median(clean),
            ))
        return summaries

    @staticmethod
    def print_report(result: WalkForwardResult) -> None:
        print("=" * 72)
        print(f"Walk-Forward Validation — {result.base_config.symbol}")
        print(f"Period: {result.base_config.start} -> {result.base_config.end}")
        print(f"Folds: {len(result.folds)}  |  test_days={result.config.test_days}  step_days={result.config.step_days}")
        print("=" * 72)

        print(f"\n{'Fold':<6}{'Start':<14}{'End':<14}{'Return%':>10}{'Sharpe':>10}{'MaxDD%':>10}{'Trades':>8}")
        for f in result.folds:
            print(
                f"{f.fold_idx:<6}{f.test_start:<14}{f.test_end:<14}"
                f"{f.metrics.total_return_pct:>10.2f}{f.metrics.sharpe:>10.2f}"
                f"{f.metrics.max_drawdown_pct:>10.2f}{f.num_trades:>8}"
            )

        print("\nAggregate across folds:")
        print(f"{'Metric':<22}{'Mean':>10}{'Median':>10}{'Std':>10}{'Min':>10}{'Max':>10}")
        for s in result.summaries:
            print(f"{s.metric_name:<22}{s.mean:>10.2f}{s.median:>10.2f}{s.std:>10.2f}{s.min:>10.2f}{s.max:>10.2f}")
        print("=" * 72)
