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


def main():
    parser = argparse.ArgumentParser(description="VN Stock Backtest Engine")
    parser.add_argument("--symbol", type=str, required=True, help="Stock symbol (e.g., VNM.HO)")
    parser.add_argument("--start", type=str, default="2023-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=datetime.now().strftime("%Y-%m-%d"), help="End date YYYY-MM-DD")
    parser.add_argument("--capital", type=float, default=100_000_000, help="Initial capital in VND")
    parser.add_argument("--strategies-dir", type=str, default="src/strategies", help="Directory containing strategy YAMLs")
    parser.add_argument("--export", action="store_true", help="Export results to CSV")
    
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
