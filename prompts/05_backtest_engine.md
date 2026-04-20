# Prompt 05 — Backtest Engine cho YAML Strategies

## Mục tiêu
Xây dựng **backtest engine đơn giản** để kiểm chứng 6 YAML strategies hiện có (`ma_crossover`, `rsi_divergence`, `volume_breakout`, `bollinger_bands`, `support_resistance`, `vn30_momentum`). Hiện tại strategies chạy hằng ngày nhưng **chưa ai biết chúng có edge thật hay không**. Backtest là bước bắt buộc trước khi tin vào signal.

Lấy cảm hứng từ paper trading engine của FinceptTerminal nhưng cài đặt tối giản, vectorized bằng pandas.

## Bối cảnh codebase
- Strategies YAML tại `src/strategies/*.yaml`, loader qua `src/scoring/strategy_runner.py::StrategyRunner.load_dir()`.
- `StrategyRunner.run(context)` nhận `IndicatorSet` (snapshot 1 thời điểm) → trả `List[ScoreCard]`. **Hiện chỉ đánh giá 1 điểm thời gian cuối DataFrame**. Backtest cần chạy rolling qua mọi ngày.
- `IndicatorEngine.compute(df)` tại `src/scoring/indicators.py` — compute một snapshot IndicatorSet từ DataFrame.
- Signal enum tại `src/scoring/signals.py`: `STRONG_BUY, BUY, BUY_WEAK, NEUTRAL, SELL_WEAK, SELL, STRONG_SELL`.
- Data source: `VNStockProvider.get_historical_data(symbol, start, end)`.

## Yêu cầu

### 1. Tạo `src/backtest/` package

```
src/backtest/
├── __init__.py
├── engine.py          # Core loop
├── portfolio.py       # Position + equity tracking
├── metrics.py         # Sharpe, CAGR, MaxDD, WinRate, etc.
└── report.py          # CLI + optional chart output
```

### 2. `src/backtest/engine.py`

```python
"""
Vectorized walk-forward backtest.

Logic:
1. Load OHLCV cho symbol từ start → end.
2. Với mỗi ngày t (từ index >= MIN_ROWS):
   - Slice df[:t+1] (tránh look-ahead bias)
   - Gọi IndicatorEngine.compute(slice) → IndicatorSet tại ngày t
   - Gọi StrategyRunner.run() → List[ScoreCard]
   - Aggregate → composite score + signal
   - Dựa trên signal + trạng thái portfolio → action (enter/exit/hold)
3. Update portfolio, tính equity curve.
4. Cuối cùng tính metrics.
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Optional
import pandas as pd


@dataclass
class BacktestConfig:
    symbol: str
    start: str                       # YYYY-MM-DD
    end: str
    initial_capital: float = 100_000_000  # 100 triệu VND
    position_size_pct: float = 1.0   # 100% NAV vào mỗi lệnh (all-in) — dễ debug
    commission_pct: float = 0.0015   # 0.15% phí (VN broker chuẩn)
    slippage_pct: float = 0.001      # 0.1% slippage
    tax_sell_pct: float = 0.001      # 0.1% thuế bán VN
    entry_signals: tuple = ("STRONG_BUY", "BUY")
    exit_signals: tuple = ("STRONG_SELL", "SELL", "SELL_WEAK")
    hold_on_neutral: bool = True     # NEUTRAL giữ nguyên, không đóng


@dataclass
class Trade:
    entry_date: date
    exit_date: Optional[date]
    entry_price: float
    exit_price: Optional[float]
    pnl_pct: Optional[float]
    hold_days: Optional[int]
    entry_signal: str
    exit_signal: Optional[str]


@dataclass
class BacktestResult:
    config: BacktestConfig
    equity_curve: pd.Series          # index=date, value=NAV
    trades: List[Trade]
    benchmark_equity: pd.Series      # Buy & hold same capital
    metrics: "BacktestMetrics"


class BacktestEngine:
    MIN_ROWS = 200  # Đủ cho MA200 + warmup

    def __init__(
        self,
        data_provider,                # VNStockProvider hoặc fallback router
        strategy_runner,              # StrategyRunner đã load
        aggregator,                   # ScoreAggregator
        indicator_engine,             # IndicatorEngine
    ):
        ...

    def run(self, config: BacktestConfig) -> BacktestResult:
        ...
```

**Chi tiết triển khai:**
- Fetch full OHLCV từ `start - 1 năm` để đủ warmup 200 phiên, nhưng **trade chỉ tính từ `start`**.
- Vòng lặp dùng index ngày chứ không datetime để tránh off-by-one.
- Position size: hiện tại 1 mã (long-only). `shares = floor(NAV * position_size_pct / entry_price_with_slippage)`.
- Entry khi signal ∈ `entry_signals` VÀ đang flat.
- Exit khi signal ∈ `exit_signals` VÀ đang long → bán toàn bộ. Trừ phí mua + phí bán + thuế bán.
- Slippage: entry giá = close * (1 + slippage), exit giá = close * (1 - slippage).
- Không short (VN không cho bán khống).
- Nếu cuối period còn position đang mở → close theo giá cuối cùng, `exit_signal = "FORCED_CLOSE"`.

### 3. `src/backtest/metrics.py`

```python
@dataclass
class BacktestMetrics:
    total_return_pct: float
    cagr_pct: float
    sharpe: float                    # Annualized
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int
    avg_hold_days: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float             # sum(wins) / |sum(losses)|
    vs_benchmark_pct: float          # total_return - benchmark_return
```

Dùng được `RiskEngine` từ Prompt 02 nếu đã merge (re-use tính Sharpe/MaxDD từ daily returns của equity_curve).

### 4. `src/backtest/report.py`

Render text report:
```
=============================================================
BACKTEST: VNM.HO | 2022-01-01 → 2024-12-31 | Cap: 100,000,000đ
=============================================================
Total Return:      +28.4%   (Benchmark B&H: +15.2%)
CAGR:              +8.7%
Sharpe:             1.12
Max Drawdown:     -18.3%
Trades:             24  (Win rate: 58.3%)
Avg Hold:           14.2 days
Avg Win:           +6.2%  | Avg Loss: -3.1%
Profit Factor:      2.01

STRATEGIES ACTIVE (per card contribution trung bình):
  ma_crossover:          22.1   | weight 1.0
  rsi_divergence:        18.5   | weight 1.0
  ...

TOP 5 TRADES:
  2023-03-14 → 2023-04-21 | +12.4% | BUY → SELL
  ...
=============================================================
```

Tuỳ chọn: xuất CSV `trades.csv` và `equity_curve.csv` vào `backtest_output/{symbol}_{start}_{end}/`.

### 5. CLI integration

Tạo subcommand qua `main.py` hoặc file riêng `backtest.py`:
```bash
python backtest.py --symbol VNM.HO --start 2022-01-01 --end 2024-12-31
python backtest.py --symbol FPT.HO --start 2022-01-01 --end 2024-12-31 --strategies ma_crossover,rsi_divergence
python backtest.py --portfolio VN30 --start 2023-01-01 --end 2024-12-31  # chạy batch cho list symbols
```

Option `--strategies` cho phép disable một số strategy (gán `enabled=False` runtime) để đo contribution riêng.

## Test
Tạo `tests/test_backtest.py`:
1. **Synthetic uptrend data** (close tăng tuyến tính 200 ngày): engine phải ra total_return > 0, num_trades >= 1.
2. **Synthetic sideways** (close ± noise, mean 0): total_return gần 0, commission làm lợi nhuận âm nhẹ.
3. **No-signal data** (indicators luôn ra NEUTRAL): num_trades == 0, equity_curve flat (trừ 0 phí).
4. **Lookahead bias check**: assert rằng khi compute indicators tại ngày t, code KHÔNG access close[t+1] (test bằng cách mock DataFrame và verify slice).
5. **Forced close**: backtest kết thúc khi đang long → trade cuối có exit_signal == "FORCED_CLOSE".

Chạy: `pytest tests/test_backtest.py -v`

## Không làm
- Không implement multi-asset portfolio (1 symbol/run là đủ; gom lại ở CLI portfolio mode).
- Không short, không leverage, không options — VN không chuẩn hoá cái này.
- Không optimize hyperparameter (grid search) — scope riêng nếu cần.
- Không live trading / paper trading broker integration.
- Không vẽ chart matplotlib mặc định — thêm flag `--plot` tuỳ chọn nếu có thời gian, không ưu tiên.

## Lưu ý hiệu năng
- 200-500 phiên × 6 strategies: mỗi phiên compute lại indicators từ đầu là **O(n²)**. Chấp nhận được cho 1 symbol, 3 năm. Nếu chậm, cache MAs rolling và chỉ compute delta.
- Không fetch remote nhiều lần — fetch 1 lần trước vòng lặp.

## Commit
```
feat(backtest): add vectorized walk-forward backtest engine for YAML strategies
```
