import argparse
import logging
import pandas as pd
from tabulate import tabulate
from src.data_provider.vnstock_provider import VNStockProvider
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator
from src.scoring.risk_metrics import RiskEngine
from src.scoring.valuation import DCFEngine
from src.screener.engine import ScreenerEngine, ScreenerConfig
from src.screener.presets import PRESETS
from src.notifier.telegram_bot import TelegramNotifier

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="VN Stock Screener - Discover top stocks in HOSE/HNX")
    parser.add_argument("--preset", choices=PRESETS.keys(), default="lynch_growth", help="Filter preset (default: lynch_growth)")
    parser.add_argument("--top", type=int, default=15, help="Number of top results to show")
    parser.add_argument("--exchange", default="HOSE,HNX", help="Exchanges to scan (comma-separated)")
    parser.add_argument("--enable-dcf", action="store_true", help="Enable DCF valuation (slow)")
    parser.add_argument("--output", choices=["text", "csv"], default="text", help="Output format")
    parser.add_argument("--notify", action="store_true", help="Send top results to Telegram")
    
    args = parser.parse_args()

    # Initialize Components
    provider = VNStockProvider()
    indicator_engine = IndicatorEngine()
    strategy_runner = StrategyRunner.load_dir("src/strategies")
    aggregator = ScoreAggregator()
    risk_engine = RiskEngine()
    dcf_engine = DCFEngine()

    engine = ScreenerEngine(
        data_provider=provider,
        indicator_engine=indicator_engine,
        strategy_runner=strategy_runner,
        aggregator=aggregator,
        risk_engine=risk_engine,
        dcf_engine=dcf_engine
    )

    # Configure Screener
    config = ScreenerConfig(
        universe_exchanges=tuple(args.exchange.split(",")),
        filters=PRESETS[args.preset](),
        top_n=args.top,
        enable_dcf=args.enable_dcf
    )

    print(f"🚀 Starting screener with preset: {args.preset} on {args.exchange}...")
    result = engine.run(config)
    
    if result.selected.empty:
        print("❌ No stocks matched the criteria.")
        return

    # Display Results
    display_cols = ["symbol", "composite_score", "final_signal", "risk_grade"]
    if "upside_pct" in result.selected.columns:
        display_cols.append("upside_pct")
    
    # Prettify for terminal
    print(f"\n✅ Top {args.top} results (Ranked by {config.rank_by}):")
    print(tabulate(result.selected[display_cols], headers='keys', tablefmt='psql', showindex=False))
    
    print(f"\n📊 Coverage: {result.coverage:.1%} | Elapsed: {result.elapsed_seconds:.1f}s")

    # Exports
    if args.output == "csv":
        fname = f"screener_{args.preset}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        result.selected.to_csv(fname, index=False)
        print(f"💾 Results saved to {fname}")

    # Notifications
    if args.notify:
        try:
            notifier = TelegramNotifier()
            # Simple summary for Telegram
            summary = f"🔥 *Stock Screener Top {args.top}* ({args.preset})\n\n"
            for _, row in result.selected.head(10).iterrows():
                summary += f"• `{row['symbol']}`: Score *{row['composite_score']:.1f}* | {row['final_signal']}\n"
            
            notifier.send_message(summary)
            print("📲 Notification sent to Telegram.")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

if __name__ == "__main__":
    main()
