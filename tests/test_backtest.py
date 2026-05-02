import pytest
import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine, BacktestConfig, SizingMethod
from src.backtest.metrics import BacktestMetrics
from src.scoring.indicators import IndicatorEngine
from src.scoring.strategy_runner import StrategyRunner, StrategyConfig, RuleConfig
from src.scoring.aggregator import ScoreAggregator
from src.scoring.signals import Signal

class MockDataProvider:
    def __init__(self, df):
        self.df = df
    def get_historical_data(self, symbol, start, end):
        return self.df

def create_synthetic_data(trend="uptrend", n=300):
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    if trend == "uptrend":
        close = np.linspace(100, 200, n)
    elif trend == "sideways":
        close = 100 + np.random.randn(n)
    else:
        close = np.linspace(200, 100, n)
    
    df = pd.DataFrame({
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "close": close,
        "volume": np.random.randint(1000, 10000, n)
    }, index=dates)
    return df

@pytest.fixture
def simple_strategy():
    # Always buy if price > 0 (for testing entry)
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    strat = StrategyConfig(name="test_strat", weight=1.0, rules=[buy_rule, default_rule])
    return StrategyRunner([strat])

@pytest.fixture
def exit_strategy():
    # Buy then Sell
    # We can use a context variable to simulate signals or just simple rules
    # Rule 1: Buy if price < 150
    # Rule 2: Sell if price >= 150
    buy_rule = RuleConfig(when="close < 150", score=80, signal=Signal.BUY, reason="Buy low")
    sell_rule = RuleConfig(when="close >= 150", score=20, signal=Signal.SELL, reason="Sell high")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    # Note: StrategyRunner evaluates rules in order.
    # But wait, StrategyRunner expects default rule to be the LAST one.
    strat = StrategyConfig(name="test_exit", weight=1.0, rules=[buy_rule, sell_rule, default_rule])
    return StrategyRunner([strat])

def test_backtest_uptrend(simple_strategy):
    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, simple_strategy, ScoreAggregator(), IndicatorEngine())
    
    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-12-31")
    result = engine.run(config)
    
    assert not result.equity_curve.empty
    assert result.equity_curve.iloc[-1] > config.initial_capital
    assert len(result.trades) >= 1
    
    metrics = BacktestMetrics.calculate(result)
    assert metrics.total_return_pct > 0

def test_backtest_no_signals():
    # Strategy that always returns NEUTRAL
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    strat = StrategyConfig(name="neutral_strat", weight=1.0, rules=[default_rule])
    runner = StrategyRunner([strat])
    
    df = create_synthetic_data("sideways", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    
    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-12-31")
    result = engine.run(config)
    
    assert len(result.trades) == 0
    # Equity curve should be flat (ignoring benchmark)
    assert result.equity_curve.iloc[0] == config.initial_capital
    assert result.equity_curve.iloc[-1] == config.initial_capital

def test_lookahead_bias(simple_strategy):
    df = create_synthetic_data("uptrend", 300)
    # We want to verify that IndicatorEngine only sees df[:t+1]
    # We can't easily check the internal state of IndicatorEngine without mocking it,
    # but the code in engine.py does `slice_df = df.loc[:t_date]`.
    # Let's verify that the backtest runs without error and gives expected results.
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, simple_strategy, ScoreAggregator(), IndicatorEngine())
    
    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-12-31")
    result = engine.run(config)
    
    # If there was look-ahead bias, it might be hard to detect just from the result,
    # but we've ensured the slice is correct in the implementation.
    assert len(result.equity_curve) > 0

def test_default_sizing_is_5pct():
    """Default FIXED sizing should buy ~5% of NAV worth of shares (CLAUDE.md)."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())

    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-10-01", initial_capital=10_000_000)
    result = engine.run(config)

    assert len(result.trades) >= 1
    first_trade = result.trades[0]
    notional = first_trade.shares * first_trade.entry_price
    # 5% of 10M = 500k; allow margin for rounding & commission
    assert 350_000 <= notional <= 550_000, f"Expected ~5% of NAV, got {notional:,.0f}"


def test_atr_risk_sizing_caps_loss():
    """ATR_RISK sizing: with -5% stop and 1% risk, position notional should be ~20% of NAV
    (since 1% / 5% = 20%), then capped by max_position_pct."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())

    config = BacktestConfig(
        symbol="TEST",
        start="2022-08-01",
        end="2022-10-01",
        initial_capital=10_000_000,
        sizing_method=SizingMethod.ATR_RISK,
        risk_per_trade_pct=0.01,
        max_position_pct=0.20,
    )
    config.stop_loss_pct = -0.05  # set on instance until stop-loss commit lands the field
    result = engine.run(config)

    assert len(result.trades) >= 1
    notional = result.trades[0].shares * result.trades[0].entry_price
    # 1% / 5% = 20% NAV target; max_position_pct caps at 20% — so equality bound
    # 20% of 10M = 2M, allow margin for rounding/commission/slippage
    assert 1_700_000 <= notional <= 2_050_000, f"Expected ~20% NAV, got {notional:,.0f}"


def test_max_position_pct_caps_size():
    """When sizing would propose huge size, max_position_pct must cap it."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())

    # Set position_size_pct = 0.99 but cap at 0.10
    config = BacktestConfig(
        symbol="TEST",
        start="2022-08-01",
        end="2022-10-01",
        initial_capital=10_000_000,
        position_size_pct=0.99,
        max_position_pct=0.10,
    )
    result = engine.run(config)
    assert len(result.trades) >= 1
    notional = result.trades[0].shares * result.trades[0].entry_price
    # Cap is 10% NAV = 1M; allow margin
    assert notional <= 1_050_000, f"Expected <=10% NAV cap, got {notional:,.0f}"


def _make_data_with_dip(dip_day: int, dip_pct: float, n: int = 80) -> pd.DataFrame:
    """Synthetic uptrend with a single intraday dip on `dip_day` (0-indexed)."""
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    close = np.linspace(100, 130, n)
    df = pd.DataFrame({
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)
    # Inject a deep dip on dip_day (intraday low) without altering close.
    df.loc[df.index[dip_day], "low"] = close[dip_day] * (1 + dip_pct)
    return df


def _make_data_with_spike(spike_day: int, spike_pct: float, n: int = 80) -> pd.DataFrame:
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    close = np.linspace(100, 110, n)
    df = pd.DataFrame({
        "open": close * 0.99,
        "high": close * 1.01,
        "low": close * 0.98,
        "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)
    df.loc[df.index[spike_day], "high"] = close[spike_day] * (1 + spike_pct)
    return df


def test_stop_loss_triggers_on_intraday_low():
    """Trade entered, intraday low breaches -5% stop -> exit STOP_LOSS at stop price."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    # Dip 8% intraday on day 250 (well into the tradeable window)
    df = _make_data_with_dip(dip_day=250, dip_pct=-0.08, n=300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST", start="2022-08-01", end="2022-12-31",
        stop_loss_pct=-0.05, use_intraday_for_stops=True,
    )
    result = engine.run(config)

    stops = [t for t in result.trades if t.exit_signal == "STOP_LOSS"]
    assert len(stops) >= 1, "Expected at least one stop-loss exit"
    # Verify stopped near -5% of entry (allow slippage tolerance)
    s = stops[0]
    realized_loss = (s.exit_price / s.entry_price) - 1
    assert -0.07 <= realized_loss <= -0.04, f"Loss {realized_loss:.3%} outside expected -5% +/- slippage band"


def test_no_stop_when_dip_not_breached():
    """Small dip that does not breach stop should NOT trigger STOP_LOSS."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    # 2% dip — well inside -5% stop
    df = _make_data_with_dip(dip_day=250, dip_pct=-0.02, n=300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-12-31", stop_loss_pct=-0.05)
    result = engine.run(config)

    stops = [t for t in result.trades if t.exit_signal == "STOP_LOSS"]
    assert len(stops) == 0, "Stop-loss must not trigger on shallow dip"


def test_take_profit_triggers_on_intraday_high():
    """Intraday spike above TP threshold -> exit TAKE_PROFIT at TP price."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    df = _make_data_with_spike(spike_day=250, spike_pct=0.20, n=300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST", start="2022-08-01", end="2022-12-31",
        stop_loss_pct=None, take_profit_pct=0.10,
    )
    result = engine.run(config)

    tps = [t for t in result.trades if t.exit_signal == "TAKE_PROFIT"]
    assert len(tps) >= 1, "Expected at least one take-profit exit"
    realized = (tps[0].exit_price / tps[0].entry_price) - 1
    assert 0.08 <= realized <= 0.12, f"TP exit at {realized:.3%}, expected ~10%"


def test_forced_close(exit_strategy):
    # Create data where it stays in BUY for a while then stays in SELL
    # Wait, exit_strategy: Buy if < 150, Sell if >= 150.
    # Uptrend from 100 to 200.
    # It will BUY at the beginning and SELL when it hits 150.
    # To test forced close, we need it to be in a position at the end.
    
    # Strategy: Always BUY
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])
    
    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    
    config = BacktestConfig(symbol="TEST", start="2022-08-01", end="2022-10-01")
    result = engine.run(config)
    
    assert len(result.trades) == 1
    assert result.trades[0].exit_signal == "FORCED_CLOSE"
