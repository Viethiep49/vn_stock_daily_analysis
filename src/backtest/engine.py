"""
Vectorized walk-forward backtest engine.
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Any
import pandas as pd
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator


@dataclass
class BacktestConfig:
    symbol: str
    start: str                       # YYYY-MM-DD
    end: str
    initial_capital: float = 100_000_000  # 100 triệu VND
    position_size_pct: float = 1.0   # 100% NAV vào mỗi lệnh (all-in)
    commission_pct: float = 0.0015   # 0.15% phí
    slippage_pct: float = 0.001      # 0.1% slippage
    tax_sell_pct: float = 0.001      # 0.1% thuế bán VN
    entry_signals: tuple = ("STRONG_BUY", "BUY")
    exit_signals: tuple = ("STRONG_SELL", "SELL", "SELL_WEAK")
    hold_on_neutral: bool = True


@dataclass
class Trade:
    entry_date: Any
    exit_date: Optional[Any] = None
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    pnl_pct: Optional[float] = None
    hold_days: Optional[int] = None
    entry_signal: str = ""
    exit_signal: Optional[str] = None
    shares: int = 0


@dataclass
class BacktestResult:
    config: BacktestConfig
    equity_curve: pd.Series          # index=date, value=NAV
    trades: List[Trade]
    benchmark_equity: pd.Series      # Buy & hold same capital
    metrics: Any = None


class BacktestEngine:
    MIN_ROWS = 200

    def __init__(
        self,
        data_provider: Any,
        strategy_runner: StrategyRunner,
        aggregator: ScoreAggregator,
        indicator_engine: IndicatorEngine,
    ):
        self.data_provider = data_provider
        self.strategy_runner = strategy_runner
        self.aggregator = aggregator
        self.indicator_engine = indicator_engine

    def run(self, config: BacktestConfig) -> BacktestResult:
        # 1. Load data. Fetch extra for warmup.
        # Ideally we need 200 sessions before 'start'
        start_date = pd.to_datetime(config.start)
        pd.to_datetime(config.end)
        
        # Approximate 1 year earlier for warmup
        warmup_start = (start_date - pd.Timedelta(days=365)).strftime("%Y-%m-%d")
        
        df = self.data_provider.get_historical_data(config.symbol, warmup_start, config.end)
        if df is None or df.empty:
            raise ValueError(f"No data for {config.symbol}")
        
        df = df.sort_index()
        
        # 2. Filter to tradeable period
        trade_indices = df.index[df.index >= start_date]
        if len(trade_indices) == 0:
            raise ValueError(f"No data within tradeable period {config.start} to {config.end}")
            
        # Initial state
        cash = config.initial_capital
        position = 0  # shares
        trades = []
        equity_values = []
        dates = []
        
        current_trade: Optional[Trade] = None
        
        # Benchmark: Buy and Hold
        first_price = df.loc[trade_indices[0], "close"]
        benchmark_shares = math.floor(config.initial_capital / (first_price * (1 + config.slippage_pct)))
        benchmark_cash = config.initial_capital - benchmark_shares * (first_price * (1 + config.slippage_pct) * (1 + config.commission_pct))
        benchmark_equity = []

        # 3. Core Loop
        for t_date in trade_indices:
            # Slice up to t (avoid look-ahead bias)
            slice_df = df.loc[:t_date]
            
            # Compute indicators & signal
            indicators = self.indicator_engine.compute(slice_df)
            cards = self.strategy_runner.run(indicators)
            report = self.aggregator.aggregate(cards)
            signal = report.final_signal.name
            
            close_price = float(slice_df.iloc[-1]["close"])
            
            # Action logic
            if position == 0:
                # Flat -> Entry?
                if signal in config.entry_signals:
                    entry_price = close_price * (1 + config.slippage_pct)
                    cost_per_share = entry_price * (1 + config.commission_pct)
                    
                    shares_to_buy = math.floor((cash * config.position_size_pct) / cost_per_share)
                    if shares_to_buy > 0:
                        total_cost = shares_to_buy * cost_per_share
                        cash -= total_cost
                        position = shares_to_buy
                        current_trade = Trade(
                            entry_date=t_date,
                            entry_price=entry_price,
                            entry_signal=signal,
                            shares=position
                        )
            else:
                # Long -> Exit?
                if signal in config.exit_signals:
                    exit_price = close_price * (1 - config.slippage_pct)
                    # Tax and commission on sell
                    proceeds = position * exit_price * (1 - config.commission_pct - config.tax_sell_pct)
                    
                    cash += proceeds
                    
                    current_trade.exit_date = t_date
                    current_trade.exit_price = exit_price
                    current_trade.exit_signal = signal
                    current_trade.pnl_pct = (exit_price / current_trade.entry_price) - 1
                    current_trade.hold_days = (pd.to_datetime(t_date) - pd.to_datetime(current_trade.entry_date)).days
                    
                    trades.append(current_trade)
                    position = 0
                    current_trade = None
            
            # Update Equity
            current_nav = cash + (position * close_price * (1 - config.commission_pct - config.tax_sell_pct) if position > 0 else 0)
            equity_values.append(current_nav)
            dates.append(t_date)
            
            # Update Benchmark
            bench_nav = benchmark_cash + (benchmark_shares * close_price)
            benchmark_equity.append(bench_nav)

        # 4. Forced Close if still open
        if position > 0 and current_trade:
            last_date = trade_indices[-1]
            last_price = float(df.loc[last_date, "close"])
            exit_price = last_price * (1 - config.slippage_pct)
            proceeds = position * exit_price * (1 - config.commission_pct - config.tax_sell_pct)
            cash += proceeds
            
            current_trade.exit_date = last_date
            current_trade.exit_price = exit_price
            current_trade.exit_signal = "FORCED_CLOSE"
            current_trade.pnl_pct = (exit_price / current_trade.entry_price) - 1
            current_trade.hold_days = (pd.to_datetime(last_date) - pd.to_datetime(current_trade.entry_date)).days
            trades.append(current_trade)
            
            # Re-update last NAV (though it should be mostly same)
            equity_values[-1] = cash

        equity_curve = pd.Series(equity_values, index=dates)
        benchmark_curve = pd.Series(benchmark_equity, index=dates)
        
        return BacktestResult(
            config=config,
            equity_curve=equity_curve,
            trades=trades,
            benchmark_equity=benchmark_curve
        )
