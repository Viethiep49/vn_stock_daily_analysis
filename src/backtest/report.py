"""
Backtest reporting.
"""
import os
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.backtest.engine import BacktestResult
    from src.backtest.metrics import BacktestMetrics


class BacktestReporter:
    def __init__(self, result: "BacktestResult", metrics: "BacktestMetrics"):
        self.result = result
        self.metrics = metrics

    def print_report(self):
        conf = self.result.config
        m = self.metrics
        
        print("=" * 65)
        print(f"BACKTEST: {conf.symbol} | {conf.start} -> {conf.end} | Cap: {conf.initial_capital:,.0f}đ")
        print("=" * 65)
        print(f"Total Return:      {m.total_return_pct:>+7.1f}%   (Benchmark B&H: {m.total_return_pct - m.vs_benchmark_pct:>+7.1f}%)")
        print(f"CAGR:              {m.cagr_pct:>+7.1f}%")
        print(f"Sharpe:             {m.sharpe:>7.2f}")
        print(f"Max Drawdown:      {m.max_drawdown_pct:>7.1f}%")
        print(f"Trades:             {m.num_trades:>5}  (Win rate: {m.win_rate_pct:.1f}%)")
        print(f"Avg Hold:           {m.avg_hold_days:>5.1f} days")
        print(f"Avg Win:           {m.avg_win_pct:>+7.1f}%  | Avg Loss: {m.avg_loss_pct:>+7.1f}%")
        print(f"Profit Factor:      {m.profit_factor:>7.2f}")
        print("-" * 65)
        
        if self.result.trades:
            print("TOP 5 TRADES (by PnL%):")
            sorted_trades = sorted(self.result.trades, key=lambda x: x.pnl_pct or 0, reverse=True)
            for t in sorted_trades[:5]:
                entry = t.entry_date.strftime("%Y-%m-%d") if hasattr(t.entry_date, "strftime") else str(t.entry_date)
                exit_d = t.exit_date.strftime("%Y-%m-%d") if t.exit_date and hasattr(t.exit_date, "strftime") else str(t.exit_date)
                print(f"  {entry} -> {exit_d} | {t.pnl_pct*100:>+6.1f}% | {t.entry_signal} -> {t.exit_signal}")
        else:
            print("NO TRADES EXECUTED.")
        print("=" * 65)

    def export_csv(self, output_dir: str = "backtest_output"):
        conf = self.result.config
        subdir = f"{conf.symbol}_{conf.start}_{conf.end}".replace("-", "")
        path = os.path.join(output_dir, subdir)
        os.makedirs(path, exist_ok=True)
        
        # 1. Equity Curve
        self.result.equity_curve.to_csv(os.path.join(path, "equity_curve.csv"))
        
        # 2. Trades
        if self.result.trades:
            trade_data = []
            for t in self.result.trades:
                trade_data.append({
                    "entry_date": t.entry_date,
                    "exit_date": t.exit_date,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "pnl_pct": t.pnl_pct,
                    "hold_days": t.hold_days,
                    "entry_signal": t.entry_signal,
                    "exit_signal": t.exit_signal,
                    "shares": t.shares
                })
            pd.DataFrame(trade_data).to_csv(os.path.join(path, "trades.csv"), index=False)
        
        print(f"Exported results to {path}")
