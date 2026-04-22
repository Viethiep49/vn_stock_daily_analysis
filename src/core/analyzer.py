import logging
import os
from typing import Dict, Any
from datetime import datetime
from src.data_provider.vnstock_provider import VNStockProvider
from src.data_provider.fallback_router import FallbackRouter
from src.utils.validator import VNStockValidator
from src.market.circuit_breaker import CircuitBreakerHandler
from src.core.llm_client import LiteLLMClient

# New Scoring Engine imports
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator
from src.scoring.explainer import LLMExplainer
from src.scoring.risk_metrics import RiskEngine
from src.scoring.valuation import DCFEngine
from src.data_provider.macro_provider import FREDMacroProvider

logger = logging.getLogger(__name__)


class Analyzer:
    """Core orchestrator for stock analysis using the Multi-Angle Scoring Engine."""

    def __init__(self, strategy_dir: str = "src/strategies"):
        # Setup data providers
        vnstock = VNStockProvider()
        self.router = FallbackRouter([vnstock])

        # Setup tools
        self.circuit_breaker = CircuitBreakerHandler()
        self.llm = LiteLLMClient()

        # Setup Scoring Pipeline
        self.indicator_engine = IndicatorEngine()
        self.strategy_runner = StrategyRunner.load_dir(strategy_dir)
        self.aggregator = ScoreAggregator()
        self.explainer = LLMExplainer(self.llm)
        self.risk_engine = RiskEngine()
        self.dcf_engine = DCFEngine()
        
        try:
            self.macro_provider = FREDMacroProvider()
        except Exception as e:
            logger.error(f"Failed to initialize FREDMacroProvider: {e}")
            self.macro_provider = None

    def analyze(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """The main analysis pipeline."""
        logger.info(f"Bắt đầu phân tích cho mã {symbol}")

        # 1. Validate
        is_valid, msg = VNStockValidator.validate(symbol)
        if not is_valid:
            return {"symbol": symbol, "error": msg, "status": "failed"}

        normalized_symbol = VNStockValidator.normalize(symbol)

        try:
            # 2. Fetch data (Info & History)
            info = self.router.execute_with_fallback(
                "get_stock_info", normalized_symbol)
            quote = self.router.execute_with_fallback(
                "get_realtime_quote", normalized_symbol)

            # Need 200 days for MA200 support
            start_date = (datetime.today() - __import__('datetime').timedelta(days=365)).strftime('%Y-%m-%d')
            df = self.router.execute_with_fallback(
                "get_historical_data",
                normalized_symbol,
                start_date,
                datetime.today().strftime('%Y-%m-%d'))

            if df.empty or len(df) < 50:
                return {
                    "symbol": normalized_symbol,
                    "status": "failed",
                    "error": "Dữ liệu lịch sử quá ít để phân tích kỹ thuật."
                }

            # 3. Indicator Engine
            indicators = self.indicator_engine.compute(df)

            # 4. Strategy Runner
            cards = self.strategy_runner.run(indicators)

            # 5. Circuit Breaker
            prev_close = indicators.prev_close
            current_price = quote.get('price', indicators.close)
            self.circuit_breaker.set_reference_price(normalized_symbol, prev_close)
            cb_status = self.circuit_breaker.check_limit_status(normalized_symbol, current_price)

            # 6. Score Aggregation
            report = self.aggregator.aggregate(cards)
            report.symbol = normalized_symbol
            report.info = info
            report.quote = quote
            report.circuit_breaker = cb_status

            # 6.1 Risk Metrics
            report.risk = self.risk_engine.compute(df)

            # 6.2 Macro Overlay
            if self.macro_provider and os.getenv("MACRO_OVERLAY_ENABLED", "true").lower() == "true":
                report.macro = self.macro_provider.get_snapshot()

            # 6.3 DCF Valuation
            try:
                bundle = self.router.execute_with_fallback("get_financials_bundle", normalized_symbol, 5)
                # KBS returns nghìn đồng, but quote.get('price') should already be normalized if we follow main.py logic
                # Actually, vnstock_provider.get_realtime_quote returns KBS original (nghìn đồng)
                market_price_vnd = quote.get('price', 0) * 1000
                valuation = self.dcf_engine.compute(bundle, market_price_vnd, industry=info.get('industry'))
                report.valuation = valuation
            except Exception as e:
                logger.warning(f"DCF failed for {normalized_symbol}: {e}")
                report.valuation = None

            # 7. AI Explanation
            narrative = self.explainer.explain(report, model=kwargs.get('model'))
            report.narrative = narrative

            # 8. Result Packaging
            tech_summary = (
                f"RSI14: {indicators.RSI14:.1f} | MACD: {indicators.MACD:.3f} (hist: {indicators.MACD_hist:.3f})\n"
                f"MA5: {indicators.MA5:.2f} | MA20: {indicators.MA20:.2f} | MA50: {indicators.MA50:.2f}\n"
                f"BB: {indicators.BB_lower:.2f} / {indicators.BB_mid:.2f} / {indicators.BB_upper:.2f}\n"
                f"ATR14: {indicators.ATR14:.2f} | Vol ratio: {indicators.volume_ratio:.2f}x\n"
                f"Support: {indicators.support_20:.2f} | Resistance: {indicators.resistance_20:.2f}"
            )

            return {
                "symbol": normalized_symbol,
                "status": "success",
                "info": info,
                "quote": quote,
                "report": report,
                "llm_analysis": narrative,
                "tech_summary": tech_summary,
                "circuit_breaker": cb_status,
                "indicators": indicators,
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            import traceback
            return {
                "symbol": symbol, 
                "error": str(e), 
                "status": "failed",
                "traceback": traceback.format_exc()
            }

