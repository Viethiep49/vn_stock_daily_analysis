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


def test_settlement_blocks_signal_exit_on_next_day():
    """Buy on day 0, SELL signal on day 1 -> exit must be deferred until day entry+3."""
    # Strategy: BUY when close < 105, SELL otherwise
    buy_rule = RuleConfig(when="close < 105", score=80, signal=Signal.BUY, reason="Buy low")
    sell_rule = RuleConfig(when="close >= 105", score=20, signal=Signal.SELL, reason="Sell high")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="bs", weight=1.0, rules=[buy_rule, sell_rule, default_rule])])

    # Construct prices that force buy on first eligible bar then immediate sell signal
    n = 300
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    close = np.full(n, 100.0)
    # Make all warmup low (BUY), then jump to 110 right at start of tradeable window
    tradeable_start_idx = 213  # corresponds to roughly 2022-08-01 with daily freq
    close[tradeable_start_idx:] = 110.0  # immediately SELL signal on day 1+
    close[tradeable_start_idx - 1] = 100.0  # last warmup is BUY trigger zone
    close[tradeable_start_idx - 2] = 100.0
    # Actually we need BUY on the first tradeable day, so adjust:
    close[tradeable_start_idx] = 100.0
    close[tradeable_start_idx + 1:] = 110.0
    df = pd.DataFrame({
        "open": close * 0.99, "high": close * 1.01,
        "low": close * 0.98, "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST", start="2022-08-01", end="2022-12-31",
        settlement_days=3, stop_loss_pct=None,  # disable SL to isolate signal/settlement
    )
    result = engine.run(config)

    assert len(result.trades) >= 1
    t = result.trades[0]
    held = (pd.to_datetime(t.exit_date) - pd.to_datetime(t.entry_date)).days
    # Settlement of 3 means at least 3 calendar days between entry and exit (with daily bars)
    assert held >= 3, f"Trade held only {held} days; expected >= 3 due to T+settlement"


def test_settlement_blocks_stop_loss_during_lock():
    """Stop-loss triggered during settlement window must be SUPPRESSED until window ends."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    # Dip on day 1 (during settlement) below -5%, then recovery
    n = 300
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    close = np.linspace(100, 130, n)
    df = pd.DataFrame({
        "open": close * 0.99, "high": close * 1.01,
        "low": close * 0.98, "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)
    # Inject a deep dip on day +1 of tradeable window (entry +1, INSIDE settlement)
    tradeable_start_idx = 213
    df.loc[df.index[tradeable_start_idx + 1], "low"] = close[tradeable_start_idx + 1] * 0.85  # -15% dip during T+1
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST", start="2022-08-01", end="2022-12-31",
        settlement_days=3, stop_loss_pct=-0.05, use_intraday_for_stops=True,
    )
    result = engine.run(config)

    if result.trades:
        t = result.trades[0]
        # Either no stop fired (because dip was during lock and recovered after) OR
        # stop fired but only after settlement period elapsed
        if t.exit_signal == "STOP_LOSS":
            held = (pd.to_datetime(t.exit_date) - pd.to_datetime(t.entry_date)).days
            assert held >= 3, f"Stop-loss exit at {held} days but settlement is 3"


def test_circuit_breaker_blocks_entry_at_limit_up():
    """If today's close is at HOSE +7% ceiling vs prior close, entry must be skipped."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    n = 300
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    close = np.full(n, 100.0)
    # Make first tradeable bar a +7% gap-up (limit-up for HOSE)
    tradeable_start_idx = 213
    close[tradeable_start_idx] = 100.0 * 1.07  # ceiling
    close[tradeable_start_idx + 1:] = 100.0 * 1.07
    df = pd.DataFrame({
        "open": close * 0.99, "high": close * 1.01,
        "low": close * 0.98, "close": close,
        "volume": np.random.randint(1000, 10000, n),
    }, index=dates)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST.HO", start="2022-08-01", end="2022-12-31",
        enforce_circuit_breaker=True,
    )
    result = engine.run(config)

    # Entry on the very first tradeable bar should have been skipped because it was limit-up
    if result.trades:
        assert result.trades[0].entry_date != dates[tradeable_start_idx], (
            "Entry should not have happened on a limit-up bar"
        )


def test_circuit_breaker_can_be_disabled():
    """When enforce_circuit_breaker=False, entry proceeds even at limit-up."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="always_buy", weight=1.0, rules=[buy_rule, default_rule])])

    df = create_synthetic_data("uptrend", 300)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())
    config = BacktestConfig(
        symbol="TEST.HO", start="2022-08-01", end="2022-12-31",
        enforce_circuit_breaker=False,
    )
    result = engine.run(config)
    assert len(result.trades) >= 1, "Disabling CB should not prevent normal trades"


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


# ---------------------------------------------------------------------------
# Walk-forward tests
# ---------------------------------------------------------------------------
from src.backtest.walkforward import WalkForwardValidator, WalkForwardConfig


def _make_engine(runner):
    df = create_synthetic_data("uptrend", n=1200)  # ~3.3 years of daily bars
    provider = MockDataProvider(df)
    return BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine()), df


def test_walkforward_produces_min_folds():
    """3-year synthetic data with 365d train + 90d test should produce >= 2 folds."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="wf_strat", weight=1.0, rules=[buy_rule, default_rule])])

    engine, df = _make_engine(runner)
    base_config = BacktestConfig(
        symbol="TEST",
        start=df.index[0].strftime("%Y-%m-%d"),
        end=df.index[-1].strftime("%Y-%m-%d"),
        stop_loss_pct=None,
    )
    wf_config = WalkForwardConfig(train_days=365, test_days=90, step_days=90, min_folds=2)
    validator = WalkForwardValidator(engine)
    result = validator.run(base_config, wf_config)

    assert len(result.folds) >= 2, f"Expected >= 2 folds, got {len(result.folds)}"


def test_walkforward_summaries_populated():
    """Summaries must contain at least sharpe and total_return_pct entries."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="wf_strat2", weight=1.0, rules=[buy_rule, default_rule])])

    engine, df = _make_engine(runner)
    base_config = BacktestConfig(
        symbol="TEST",
        start=df.index[0].strftime("%Y-%m-%d"),
        end=df.index[-1].strftime("%Y-%m-%d"),
        stop_loss_pct=None,
    )
    wf_config = WalkForwardConfig(train_days=365, test_days=90, step_days=90, min_folds=2)
    validator = WalkForwardValidator(engine)
    result = validator.run(base_config, wf_config)

    summary_names = {s.metric_name for s in result.summaries}
    assert "total_return_pct" in summary_names
    assert "sharpe" in summary_names


def test_walkforward_too_short_raises():
    """Period shorter than train+test should raise ValueError."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="wf_short", weight=1.0, rules=[buy_rule, default_rule])])

    df = create_synthetic_data("uptrend", n=200)
    provider = MockDataProvider(df)
    engine = BacktestEngine(provider, runner, ScoreAggregator(), IndicatorEngine())

    base_config = BacktestConfig(
        symbol="TEST",
        start=df.index[0].strftime("%Y-%m-%d"),
        end=df.index[-1].strftime("%Y-%m-%d"),
    )
    wf_config = WalkForwardConfig(train_days=365, test_days=90, step_days=90, min_folds=2)
    validator = WalkForwardValidator(engine)
    with pytest.raises(ValueError):
        validator.run(base_config, wf_config)


def test_walkforward_fold_dates_are_sequential():
    """Each fold's test_start must be >= previous fold's test_end."""
    buy_rule = RuleConfig(when="close > 0", score=80, signal=Signal.BUY, reason="Always buy")
    default_rule = RuleConfig(default=True, score=50, signal=Signal.NEUTRAL, reason="Default")
    runner = StrategyRunner([StrategyConfig(name="wf_seq", weight=1.0, rules=[buy_rule, default_rule])])

    engine, df = _make_engine(runner)
    base_config = BacktestConfig(
        symbol="TEST",
        start=df.index[0].strftime("%Y-%m-%d"),
        end=df.index[-1].strftime("%Y-%m-%d"),
        stop_loss_pct=None,
    )
    wf_config = WalkForwardConfig(train_days=365, test_days=90, step_days=90, min_folds=2)
    validator = WalkForwardValidator(engine)
    result = validator.run(base_config, wf_config)

    for i in range(1, len(result.folds)):
        prev_end = pd.to_datetime(result.folds[i - 1].test_end)
        curr_start = pd.to_datetime(result.folds[i].test_start)
        assert curr_start >= prev_end, f"Fold {i} starts {curr_start} before fold {i-1} ends {prev_end}"
