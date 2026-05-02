"""
Vectorized walk-forward backtest engine.
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any
import pandas as pd
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator


class SizingMethod(str, Enum):
    FIXED = "fixed"
    ATR_RISK = "atr_risk"


@dataclass
class BacktestConfig:
    symbol: str
    start: str                       # YYYY-MM-DD
    end: str
    initial_capital: float = 100_000_000  # 100 triệu VND
    sizing_method: SizingMethod = SizingMethod.FIXED
    position_size_pct: float = 0.05  # 5% NAV per trade (FIXED method); matches CLAUDE.md
    risk_per_trade_pct: float = 0.01  # 1% NAV at risk per trade (ATR_RISK method)
    max_position_pct: float = 0.20    # cap to 20% NAV regardless of sizing method
    commission_pct: float = 0.0015   # 0.15% phí
    slippage_pct: float = 0.001      # 0.1% slippage
    tax_sell_pct: float = 0.001      # 0.1% thuế bán VN
    entry_signals: tuple = ("STRONG_BUY", "BUY")
    exit_signals: tuple = ("STRONG_SELL", "SELL", "SELL_WEAK")
    hold_on_neutral: bool = True
    stop_loss_pct: Optional[float] = -0.05   # -5% per CLAUDE.md; None disables
    take_profit_pct: Optional[float] = None  # e.g. 0.15 for +15%; None disables
    use_intraday_for_stops: bool = True      # use day's low/high to detect trigger


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

                    nav = cash  # flat -> NAV equals cash
                    shares_to_buy = self._size_position(
                        config=config,
                        nav=nav,
                        entry_price=entry_price,
                        cost_per_share=cost_per_share,
                        indicators=indicators,
                    )
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
                # Long -> evaluate exits in priority order: stop-loss > take-profit > signal.
                bar_row = slice_df.iloc[-1]
                stop_exit = self._check_stop_exit(
                    config=config,
                    entry_price=current_trade.entry_price,
                    bar_high=float(bar_row.get("high", bar_row["close"])),
                    bar_low=float(bar_row.get("low", bar_row["close"])),
                    bar_close=close_price,
                )

                exit_label: Optional[str] = None
                raw_exit_price: Optional[float] = None

                if stop_exit is not None:
                    raw_exit_price, exit_label = stop_exit
                elif signal in config.exit_signals:
                    raw_exit_price = close_price
                    exit_label = signal

                if exit_label is not None:
                    exit_price = raw_exit_price * (1 - config.slippage_pct)
                    proceeds = position * exit_price * (1 - config.commission_pct - config.tax_sell_pct)
                    cash += proceeds

                    current_trade.exit_date = t_date
                    current_trade.exit_price = exit_price
                    current_trade.exit_signal = exit_label
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

    def _check_stop_exit(
        self,
        config: BacktestConfig,
        entry_price: float,
        bar_high: float,
        bar_low: float,
        bar_close: float,
    ) -> Optional[tuple]:
        """
        Decide whether stop-loss or take-profit triggers on this bar.
        Returns (raw_fill_price, exit_label) or None.

        When intraday is enabled, uses bar_low for stop and bar_high for TP
        (i.e. assumes the worst-case touch at the configured level). If the
        bar opened past the level, the stop is filled at the configured
        threshold rather than the gap-down price — a deliberate optimistic
        approximation since we don't model open/gap separately here.
        """
        sl_pct = config.stop_loss_pct
        tp_pct = config.take_profit_pct

        if sl_pct is not None:
            stop_price = entry_price * (1 + sl_pct)
            trigger_price = bar_low if config.use_intraday_for_stops else bar_close
            if trigger_price <= stop_price:
                return (stop_price, "STOP_LOSS")

        if tp_pct is not None:
            tp_price = entry_price * (1 + tp_pct)
            trigger_price = bar_high if config.use_intraday_for_stops else bar_close
            if trigger_price >= tp_price:
                return (tp_price, "TAKE_PROFIT")

        return None

    def _size_position(
        self,
        config: BacktestConfig,
        nav: float,
        entry_price: float,
        cost_per_share: float,
        indicators: Any,
    ) -> int:
        """
        Compute number of shares to buy.

        FIXED: spend `position_size_pct * NAV`.
        ATR_RISK: size so a stop-out at `stop_loss_pct` loses ~`risk_per_trade_pct * NAV`.
                  Falls back to FIXED if stop-loss is not configured.

        Always clamped by `max_position_pct * NAV`.
        """
        if cost_per_share <= 0 or nav <= 0:
            return 0

        max_shares = math.floor((nav * config.max_position_pct) / cost_per_share)

        stop_pct = getattr(config, "stop_loss_pct", None)

        if config.sizing_method == SizingMethod.ATR_RISK and stop_pct:
            risk_per_share = entry_price * abs(stop_pct)
            if risk_per_share <= 0:
                return 0
            target_shares = math.floor((nav * config.risk_per_trade_pct) / risk_per_share)
        else:
            target_shares = math.floor((nav * config.position_size_pct) / cost_per_share)

        return max(0, min(target_shares, max_shares))
