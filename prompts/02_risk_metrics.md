# Prompt 02 — Thêm VaR + Sharpe + Max Drawdown vào Scoring Engine

## Mục tiêu
Bổ sung module **Risk Metrics** lấy cảm hứng từ QuantLib suite của FinceptTerminal (18 module: VaR, Sharpe, v.v.) nhưng cài đặt thuần Python bằng numpy/pandas. Các chỉ số rủi ro phải được:
1. Tính từ OHLCV đã có sẵn
2. Gắn vào `AnalysisReport`
3. Hiển thị trong báo cáo Telegram & Discord

## Bối cảnh codebase
- Scoring engine tại `src/scoring/`. Các module liên quan:
  - `indicators.py` — `IndicatorEngine.compute(df)` → `IndicatorSet` (chỉ chứa chỉ báo kỹ thuật, KHÔNG có rủi ro).
  - `aggregator.py` — `AnalysisReport` là dataclass có các field: `composite`, `final_signal`, `cards`, `narrative`, `symbol`, `info`, `quote`, `circuit_breaker`.
  - `fundamental.py` — hiện chỉ có Piotroski F-Score.
- Analyzer gọi scoring: `src/core/analyzer.py` (đọc để biết chỗ inject).
- Notifier: `src/notifier/telegram_bot.py` và `src/notifier/discord_bot.py` render từ `report_data['report']` (AnalysisReport).
- Dataframe input có cột: `date, open, high, low, close, volume`.

## Yêu cầu

### 1. Tạo file mới `src/scoring/risk_metrics.py`

```python
"""Risk metrics: VaR, Sharpe, Max Drawdown, Volatility — tính từ OHLCV."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class RiskMetrics:
    volatility_annual: Optional[float]   # %/năm, dựa trên daily returns * sqrt(252)
    sharpe_ratio: Optional[float]        # (mean_ret - rf) / std, annualized
    sortino_ratio: Optional[float]       # Sharpe nhưng dùng downside deviation
    var_95_1d: Optional[float]           # Historical VaR 95% 1 ngày, đơn vị %
    cvar_95_1d: Optional[float]          # Expected Shortfall (CVaR) 95%
    max_drawdown: Optional[float]        # % sụt giảm tối đa từ peak, giá trị âm
    current_drawdown: Optional[float]    # % drawdown tại thời điểm hiện tại
    risk_grade: str                      # "LOW" | "MEDIUM" | "HIGH" | "EXTREME"


class RiskEngine:
    """
    Tính các chỉ số rủi ro từ OHLCV (cần >= 60 phiên để đáng tin).
    Risk-free rate mặc định 4.5%/năm (xấp xỉ lãi suất kỳ hạn 12T VN).
    """
    MIN_ROWS = 60
    TRADING_DAYS = 252

    def __init__(self, risk_free_rate: float = 0.045):
        self.rf = risk_free_rate

    def compute(self, df: pd.DataFrame) -> RiskMetrics:
        # TODO: implement
        ...
```

**Chi tiết cần triển khai:**
- `returns = close.pct_change().dropna()`
- `volatility_annual = returns.std() * sqrt(252) * 100`
- `sharpe = (returns.mean() * 252 - rf) / (returns.std() * sqrt(252))`
- `sortino`: dùng `returns[returns < 0].std() * sqrt(252)` làm mẫu số
- `var_95_1d = np.percentile(returns, 5) * 100` (giá trị âm, đơn vị %)
- `cvar_95_1d = returns[returns <= np.percentile(returns, 5)].mean() * 100`
- `max_drawdown`:
  ```python
  cum = (1 + returns).cumprod()
  peak = cum.cummax()
  dd = (cum - peak) / peak
  max_drawdown = dd.min() * 100
  current_drawdown = dd.iloc[-1] * 100
  ```
- `risk_grade`: dựa trên `volatility_annual`:
  - `< 25%` → LOW
  - `25–40%` → MEDIUM
  - `40–60%` → HIGH
  - `>= 60%` → EXTREME
- Nếu `len(df) < MIN_ROWS`, trả về `RiskMetrics` với mọi field `None` trừ `risk_grade="UNKNOWN"`.

### 2. Gắn vào `AnalysisReport`

Sửa `src/scoring/aggregator.py`:
- Thêm `risk: Optional["RiskMetrics"] = None` vào dataclass `AnalysisReport`.
- **KHÔNG** import trực tiếp `RiskMetrics` để tránh circular import — dùng `TYPE_CHECKING` hoặc forward reference `"RiskMetrics"`.

### 3. Tích hợp vào Analyzer

Sửa `src/core/analyzer.py`:
- Đọc code hiện tại trước khi sửa.
- Sau khi đã có `historical_df`, thêm:
  ```python
  from src.scoring.risk_metrics import RiskEngine
  risk = RiskEngine().compute(historical_df)
  ```
- Gán `report.risk = risk` trước khi trả về.

### 4. Hiển thị trong Telegram

Sửa `src/notifier/telegram_bot.py` — thêm đoạn sau score_text:
```
📉 *Rủi ro* (`{risk_grade}`):
  • Volatility: `{vol:.1f}%/năm`
  • Sharpe: `{sharpe:.2f}` | Sortino: `{sortino:.2f}`
  • VaR 95% 1D: `{var:.2f}%`
  • Max DD: `{mdd:.1f}%` | Hiện tại DD: `{cdd:.1f}%`
```
Skip section nếu `report.risk is None` hoặc `risk_grade == "UNKNOWN"`.

### 5. Hiển thị trong Discord

Sửa `src/notifier/discord_bot.py` — thêm 1 field embed mới `"📉 Rủi ro"` cùng format tương tự, đặt **sau** `breakdown_field`.

Màu embed điều chỉnh: nếu `risk_grade in ("HIGH", "EXTREME")` thì ưu tiên màu đỏ bất kể signal.

## Test
Tạo `tests/test_risk_metrics.py`:
1. Test với DataFrame 300 ngày giá random — đảm bảo mọi field `not None`.
2. Test với DataFrame 30 ngày — đảm bảo `risk_grade == "UNKNOWN"` và các field rủi ro là `None`.
3. Test với giá constant (không biến động) — `volatility ≈ 0`, `sharpe` xử lý chia 0 an toàn (trả `None`, không raise).
4. Test max_drawdown âm với chuỗi giá giảm đều.

Chạy: `pytest tests/test_risk_metrics.py -v`

## Không làm
- Không thêm dependency (numpy đã có qua pandas).
- Không sửa YAML strategies — risk không phải là 1 strategy trong ScoreCard, mà là metadata đi kèm.
- Không thay đổi logic tính composite score — risk chỉ để hiển thị và cảnh báo, không điều chỉnh điểm (trừ khi user yêu cầu sau).

## Commit
```
feat(scoring): add VaR / Sharpe / Sortino / MaxDD risk metrics to AnalysisReport
```
