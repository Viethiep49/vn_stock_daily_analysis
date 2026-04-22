"""
Backtest metrics calculation.
"""
from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from src.backtest.engine import BacktestResult


@dataclass
class BacktestMetrics:
    total_return_pct: float
    cagr_pct: float
    sharpe: float                    # Annualized
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int
    avg_hold_days: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    vs_benchmark_pct: float

    @classmethod
    def calculate(cls, result: "BacktestResult") -> "BacktestMetrics":
        equity = result.equity_curve
        benchmark = result.benchmark_equity
        trades = result.trades

        if equity.empty:
            return cls.empty()

        # Total Return
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1

        # CAGR
        days = (equity.index[-1] - equity.index[0]).days
        if days > 0:
            cagr = (1 + total_return) ** (365 / days) - 1
        else:
            cagr = 0.0

        # Sharpe Ratio (assuming 0% risk free rate)
        returns = equity.pct_change().dropna()
        if len(returns) > 1 and returns.std() != 0:
            # Annualized Sharpe: (mean / std) * sqrt(252)
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe = 0.0

        # Max Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_dd = drawdown.min()

        # Trade metrics
        num_trades = len(trades)
        if num_trades > 0:
            pnls = [t.pnl_pct for t in trades if t.pnl_pct is not None]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]
            
            win_rate = len(wins) / num_trades if num_trades > 0 else 0
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            
            profit_factor = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else float('inf') if wins else 0
            
            avg_hold = np.mean([t.hold_days for t in trades if t.hold_days is not None])
        else:
            win_rate = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            profit_factor = 0.0
            avg_hold = 0.0

        # vs Benchmark
        bench_return = (benchmark.iloc[-1] / benchmark.iloc[0]) - 1
        vs_benchmark = total_return - bench_return

        return cls(
            total_return_pct=total_return * 100,
            cagr_pct=cagr * 100,
            sharpe=sharpe,
            max_drawdown_pct=max_dd * 100,
            win_rate_pct=win_rate * 100,
            num_trades=num_trades,
            avg_hold_days=avg_hold,
            avg_win_pct=avg_win * 100,
            avg_loss_pct=avg_loss * 100,
            profit_factor=profit_factor,
            vs_benchmark_pct=vs_benchmark * 100
        )

    @classmethod
    def empty(cls) -> "BacktestMetrics":
        return cls(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
