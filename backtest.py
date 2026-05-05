"""
CLI for Backtesting VN Stocks.
"""
import argparse
import sys
import os
from datetime import datetime

# Add src to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.data_provider.vnstock_provider import VNStockProvider
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator
from src.scoring.indicators import IndicatorEngine
from src.backtest.engine import BacktestEngine, BacktestConfig
from src.backtest.metrics import BacktestMetrics
from src.backtest.report import BacktestReporter
from src.backtest.walkforward import WalkForwardValidator, WalkForwardConfig


def main():
    parser = argparse.ArgumentParser(description="VN Stock Backtest Engine")
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol (e.g., VNM.HO)")
    parser.add_argument("--start", type=str, default="2023-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="End date YYYY-MM-DD")
    parser.add_argument("--capital", type=float, default=100_000_000, help="Initial capital in VND")
    parser.add_argument("--strategies-dir", type=str, default="src/strategies", help="Directory containing strategy YAMLs")
    parser.add_argument("--export", action="store_true", help="Export results to CSV")
    parser.add_argument("--walkforward", action="store_true", help="Run walk-forward rolling validation")
    parser.add_argument("--train-days", type=int, default=365, help="Warmup days before each test fold")
    parser.add_argument("--test-days", type=int, default=90, help="Length of each test fold in days")
    parser.add_argument("--step-days", type=int, default=90, help="Step between folds (default = test-days)")

    args = parser.parse_args()

    # 1. Setup components
    data_provider = VNStockProvider()
    strategy_runner = StrategyRunner.load_dir(args.strategies_dir)
    aggregator = ScoreAggregator()
    indicator_engine = IndicatorEngine()
    
    engine = BacktestEngine(
        data_provider=data_provider,
        strategy_runner=strategy_runner,
        aggregator=aggregator,
        indicator_engine=indicator_engine
    )
    
    # 2. Config
    config = BacktestConfig(
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        initial_capital=args.capital
    )
    
    # 3. Run
    if args.walkforward:
        from src.backtest.walkforward import WalkForwardValidator, WalkForwardConfig
        wf_config = WalkForwardConfig(
            train_days=args.train_days,
            test_days=args.test_days,
            step_days=args.step_days,
        )
        validator = WalkForwardValidator(engine)
        print(f"Running walk-forward for {args.symbol} from {args.start} to {args.end} "
              f"(train={args.train_days}d, test={args.test_days}d, step={args.step_days}d)...")
        try:
            wf_result = validator.run(config, wf_config)
        except Exception as e:
            print(f"Error during walk-forward: {e}")
            sys.exit(1)
        WalkForwardValidator.print_report(wf_result)
        if args.export:
            import csv
            out_path = f"walkforward_{args.symbol}_{args.start}_{args.end}.csv"
            with open(out_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["fold", "test_start", "test_end", "return_pct", "sharpe", "max_dd_pct", "trades"])
                for fold in wf_result.folds:
                    w.writerow([
                        fold.fold_idx, fold.test_start, fold.test_end,
                        round(fold.metrics.total_return_pct, 4),
                        round(fold.metrics.sharpe, 4),
                        round(fold.metrics.max_drawdown_pct, 4),
                        fold.num_trades,
                    ])
            print(f"Walk-forward results exported to {out_path}")
        return

    print(f"Running backtest for {args.symbol} from {args.start} to {args.end}...")
    try:
        result = engine.run(config)
    except Exception as e:
        print(f"Error during backtest: {e}")
        sys.exit(1)

    # 4. Metrics & Report
    metrics = BacktestMetrics.calculate(result)
    reporter = BacktestReporter(result, metrics)

    reporter.print_report()

    if args.export:
        reporter.export_csv()


if __name__ == "__main__":
    main()
