# Backtest & Risk Hardening — Design Spec

Date: 2026-05-03
Scope: `src/backtest/engine.py`, `src/backtest/walkforward.py` (new), `src/market/circuit_breaker.py` integration

## Problem

The current backtest engine produces optimistically biased results that cannot be trusted to evaluate real-money strategies on the Vietnamese market. Five concrete defects:

1. **No stop-loss.** `CLAUDE.md` states a target of "-5% fixed stop loss"; the engine never reads any stop-loss config. Trades only exit on a SELL signal or end-of-period forced close, allowing arbitrarily deep drawdowns per trade.
2. **Position size default is 100% NAV.** `BacktestConfig.position_size_pct = 1.0` (engine.py:19). All-in on every signal contradicts the documented 5% sizing and produces unrealistic equity curves.
3. **No T+2.5 settlement.** Vietnamese regulation forbids selling shares for ~2.5 trading days after purchase. The engine permits buy on T and sell on T+1, inflating profitable scalps that cannot occur in production.
4. **No walk-forward validation.** The engine runs a single train/test slice with overlapping warmup. Reported metrics may be heavily overfit to the chosen window.
5. **Circuit breaker ignored.** `CircuitBreakerHandler` (src/market/circuit_breaker.py) detects ceiling/floor but the backtest fills entries at limit-up and exits at limit-down — prices that have effectively zero liquidity in reality.

## Goals

- Make backtest metrics directionally trustworthy for real-money decisions on HOSE/HNX/UPCOM.
- Default behaviour matches a conservative retail trader (5% size, -5% stop) without forcing every caller to reconfigure.
- All changes covered by tests; no regressions to existing tests.
- Out of scope: ML model retraining, multi-asset portfolios, intraday simulation, optimisation framework.

## Design

### 1. Position sizing

Add to `BacktestConfig`:

```python
class SizingMethod(str, Enum):
    FIXED = "fixed"        # use position_size_pct of NAV
    ATR_RISK = "atr_risk"  # size so that stop_loss_pct loss == risk_per_trade_pct of NAV

sizing_method: SizingMethod = SizingMethod.FIXED
position_size_pct: float = 0.05        # was 1.0 — now matches CLAUDE.md
risk_per_trade_pct: float = 0.01       # 1% NAV at risk per trade
max_position_pct: float = 0.20         # cap when ATR_RISK proposes huge size
```

For `ATR_RISK`: `shares = (NAV * risk_per_trade_pct) / (entry_price * abs(stop_loss_pct))`, clamped to `max_position_pct * NAV / entry_price`. This is the textbook fixed-fractional-risk sizing — losses on a stop-out are bounded to roughly `risk_per_trade_pct` of NAV regardless of volatility.

### 2. Stop-loss / take-profit

Add to `BacktestConfig`:

```python
stop_loss_pct: float | None = -0.05    # -5% fixed; None disables
take_profit_pct: float | None = None   # e.g. 0.15 for +15%; None disables
use_intraday_for_stops: bool = True    # use day's low/high to detect trigger
```

Eval order each bar while in a position (BEFORE signal logic):
1. If `use_intraday_for_stops` and `low <= entry_price * (1 + stop_loss_pct)`: exit at `entry_price * (1 + stop_loss_pct)` minus slippage. Mark `exit_signal="STOP_LOSS"`.
2. Else if take-profit configured and `high >= entry_price * (1 + take_profit_pct)`: exit at TP price. Mark `exit_signal="TAKE_PROFIT"`.
3. Else fall through to signal-based exit.

Using intraday low/high reflects realistic stop fills. If `low/high` columns are missing, fall back to close.

**T+2.5 interaction:** stop-loss is a hard risk control and SHOULD respect settlement — selling on T+1 is illegal regardless of stop trigger. So stops queue until the earliest legal exit day; the engine still records the stop trigger at trigger time and exits at the next legal day's price.

### 3. T+2.5 settlement

Track `entry_bar_idx` on `Trade`. Vietnamese T+2.5: shares purchased on day T are tradeable from day T+2.5 onward — the conservative interpretation used here is **cannot exit until idx >= entry_idx + 3**. This treats T+2 partial as not yet tradeable.

Apply to:
- Signal-based exits — defer to first eligible bar; re-check signal there.
- Stop-loss / take-profit — record trigger date, but execute exit on first eligible bar at that bar's open price (worst-case fill modelling).

Add `settlement_days: int = 3` config (allows toggling for unit tests).

### 4. Circuit breaker integration

Inject a `CircuitBreakerHandler` (optional; default constructed if not provided). At each bar before entry/exit:

- Compute price limits using prior bar's close as reference price.
- **Entry blocked** if today's close >= ceiling \* (1 - 0.001). Cannot reliably fill at limit-up.
- **Exit blocked** if today's close <= floor \* (1 + 0.001). Cannot reliably sell at limit-down — defer to next bar.

Make the handler aware of exchange via `BacktestConfig.exchange: Literal["HO", "HN", "UPC"] = "HO"` (parsed from symbol if `.HO`/`.HN`/`.UPC` suffix present).

### 5. Walk-forward validator

New module `src/backtest/walkforward.py`:

```python
@dataclass
class WalkForwardConfig:
    train_days: int = 365
    test_days: int = 90
    step_days: int = 90        # rolling step; for anchored, set step = test
    mode: Literal["rolling", "anchored"] = "rolling"

class WalkForwardValidator:
    def run(self, base_config: BacktestConfig, df: pd.DataFrame) -> WalkForwardResult: ...
```

`WalkForwardResult` carries a list of per-fold `BacktestMetrics` plus aggregate stats (mean/median/std/min/max for Sharpe, MaxDD, total_return, win_rate, num_trades). Reporter prints both.

CLI: `python backtest.py --symbol MBB.HO --walkforward --train-days 365 --test-days 90`.

Out of scope: parameter optimisation per fold (would invite overfitting at this stage).

## Test plan

Each fix lands in its own commit, gated by tests in `tests/test_backtest.py`:

1. **Sizing** — assert FIXED at 0.05 buys ~5% of NAV worth of shares; ATR_RISK with -5% stop and 1% risk produces ~20% position by mathematical identity; `max_position_pct` cap respected.
2. **Stop-loss** — synthetic data with sharp dip below -5% from entry → trade exits with `STOP_LOSS` signal at expected price; small dip not breaching -5% → no early exit.
3. **Take-profit** — symmetric test with upward spike.
4. **T+2.5** — buy on day 0, signal SELL on day 1 → exit deferred to day 3; stop trigger on day 1 → execution on day 3.
5. **Circuit breaker** — synthetic data where signal day equals limit-up → entry skipped, no trade opened. Limit-down on exit signal → exit deferred to next non-limit day.
6. **Walk-forward** — synthetic 3-year series, 365/90 rolling → produces ≥6 folds, aggregate metrics dataclass populated correctly.

Plus: existing tests in `test_backtest.py` must keep passing (with synthetic data they may need minor adjustment given new 5% sizing default — uptrend test still expects positive return, just smaller).

## Risk & rollout

- New defaults ARE breaking for callers who relied on 100% sizing or no-stop behaviour. This is intentional: prior defaults were unsafe. Document in commit messages; existing test that asserts uptrend produces profit will be relaxed to assert positive return only.
- T+2.5 will reduce trade count and apparent return in many backtests. This is correctness, not regression — note in spec.
- No production runtime impact: the FastAPI/Next.js dashboard does not use BacktestEngine in hot path. CLI users will see different numbers.

## Non-goals (explicit)

- Multi-symbol / portfolio-level backtest
- Intraday bar simulation
- Optimal parameter search / hyperparam tuning
- Crypto support (separate spec if needed)
- Replacing the existing scoring/agent stack
