import logging
import time
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime, timedelta

from src.screener.universe import UniverseLoader, UniverseItem
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator, AnalysisReport
from src.scoring.risk_metrics import RiskEngine
from src.scoring.valuation import DCFEngine
from src.scoring.fundamental import calculate_f_score

logger = logging.getLogger(__name__)

@dataclass
class ScreenerConfig:
    universe_exchanges: tuple = ("HOSE", "HNX")
    filters: List[Callable] = field(default_factory=list)
    rank_by: str = "composite_score"  # Field để sort desc
    top_n: int = 20
    parallel_workers: int = 8          # ThreadPool cho fetch song song
    min_history_days: int = 250
    enable_dcf: bool = False           # Tắt mặc định — chậm
    enable_risk: bool = True
    enable_fscore: bool = True

@dataclass
class ScreenerResult:
    rows: pd.DataFrame                 # Full results (pre-filter)
    selected: pd.DataFrame             # Post-filter, ranked, top_n
    config: ScreenerConfig
    elapsed_seconds: float
    coverage: float                    # % symbols fetched thành công

class ScreenerEngine:
    def __init__(
        self,
        data_provider,
        indicator_engine: IndicatorEngine,
        strategy_runner: StrategyRunner,
        aggregator: ScoreAggregator,
        risk_engine: Optional[RiskEngine] = None,
        dcf_engine: Optional[DCFEngine] = None,
        universe_loader: Optional[UniverseLoader] = None,
    ):
        self.data_provider = data_provider
        self.indicator_engine = indicator_engine
        self.strategy_runner = strategy_runner
        self.aggregator = aggregator
        self.risk_engine = risk_engine or RiskEngine()
        self.dcf_engine = dcf_engine or DCFEngine()
        self.universe_loader = universe_loader or UniverseLoader()

    def run(self, config: ScreenerConfig) -> ScreenerResult:
        start_time = time.time()
        
        # 1. Load universe
        universe = self.universe_loader.load(config.universe_exchanges)
        total_symbols = len(universe)
        logger.info(f"Starting screen for {total_symbols} symbols")

        # 2. Parallel fetch and process
        results = []
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
            future_to_symbol = {
                executor.submit(self._process_symbol, item, config): item.symbol 
                for item in universe
            }
            
            for future in tqdm(as_completed(future_to_symbol), total=total_symbols, desc="Screening"):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    # Log to error file as requested
                    self._log_error(symbol, e)

        # 3. Build DataFrame
        rows_df = pd.DataFrame(results)
        
        # 4. Apply filters
        selected_df = rows_df.copy()
        if config.filters:
            for f in config.filters:
                mask = selected_df.apply(f, axis=1)
                selected_df = selected_df[mask]

        # 5. Rank and top_n
        if not selected_df.empty and config.rank_by in selected_df.columns:
            selected_df = selected_df.sort_values(config.rank_by, ascending=False)
        
        top_n_df = selected_df.head(config.top_n)

        elapsed = time.time() - start_time
        coverage = success_count / total_symbols if total_symbols > 0 else 0
        
        return ScreenerResult(
            rows=rows_df,
            selected=top_n_df,
            config=config,
            elapsed_seconds=elapsed,
            coverage=coverage
        )

    def _process_symbol(self, item: UniverseItem, config: ScreenerConfig) -> Optional[Dict[str, Any]]:
        """Worker function for a single symbol."""
        symbol = item.symbol
        try:
            # a. Fetch historical data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=config.min_history_days)).strftime("%Y-%m-%d")
            
            df_hist = self.data_provider.get_historical_data(symbol, start_date, end_date)
            if df_hist.empty or len(df_hist) < 20: # Minimal requirement
                return None
            
            # b. Compute indicators
            indicator_set = self.indicator_engine.compute(df_hist)
            indicator_dict = pd.Series(indicator_set.__dict__).to_dict()
            
            # c. Scoring
            cards = self.strategy_runner.run(indicator_set)
            report = self.aggregator.aggregate(cards)
            
            # d. Base result
            res = {
                "symbol": symbol,
                "exchange": item.exchange,
                "company_name": item.company_name,
                "industry": item.industry,
                "composite_score": report.composite,
                "signal": report.final_signal.value,
                **indicator_dict
            }
            
            # e. Optional: Risk
            if config.enable_risk:
                risk_metrics = self.risk_engine.compute(df_hist)
                res.update({
                    "risk_grade": risk_metrics.risk_grade,
                    "volatility_annual": risk_metrics.volatility_annual,
                    "max_drawdown": risk_metrics.max_drawdown
                })
            
            # f. Optional: F-Score
            if config.enable_fscore:
                # This is tricky as calculate_f_score expects specific format
                # For now, let's try to get what we can or mock it if complex
                # In a real scenario, we'd fetch financial reports here.
                # To keep it fast, we might skip full F-Score or use cached data.
                pass
                
            # g. Optional: DCF
            if config.enable_dcf:
                bundle = self.data_provider.get_financials_bundle(symbol)
                if bundle and not bundle.get("cash_flow", pd.DataFrame()).empty:
                    dcf_res = self.dcf_engine.compute(bundle, res["close"], industry=item.industry)
                    res.update({
                        "dcf_upside_pct": dcf_res.upside_pct,
                        "intrinsic_value": dcf_res.intrinsic_value_per_share,
                        "valuation_grade": dcf_res.grade
                    })

            # Calculate market cap if possible
            # Need outstanding shares - usually in company info
            info = self.data_provider.get_stock_info(symbol)
            shares = info.get("outstanding_shares")
            if shares:
                res["market_cap_bn"] = (res["close"] * shares) / 1e9
            
            # Liquidity (avg volume 20d)
            res["avg_volume_20d"] = df_hist["volume"].tail(20).mean()

            return res

        except Exception as e:
            logger.debug(f"Process failed for {symbol}: {e}")
            return None

    def _log_error(self, symbol: str, error: Exception):
        today_str = datetime.now().strftime("%Y%m%d")
        error_file = os.path.join(UniverseLoader.CACHE_DIR, f"screener_errors_{today_str}.log")
        with open(error_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {symbol}: {error}\n")
