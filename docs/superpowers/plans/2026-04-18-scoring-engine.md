# Multi-Angle Scoring Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Biến 6 YAML strategies thành các "góc nhìn" chấm điểm 0-100 độc lập, tổng hợp thành composite score; LLM chỉ giải thích — không chấm điểm.

**Architecture:** Pipeline mới `DataProvider → IndicatorEngine → StrategyRunner → ScoreAggregator → LLMExplainer → Notifier`. Mỗi lớp có trách nhiệm đơn, test độc lập. Spec chi tiết: `docs/superpowers/specs/2026-04-18-scoring-engine-design.md`.

**Tech Stack:** Python 3.11+, pandas, pandas-ta, Pydantic v2, asteval, pytest, PyYAML, LiteLLM (đã có).

---

## File Structure

**Tạo mới:**
- `src/scoring/__init__.py` — package marker
- `src/scoring/signals.py` — `Signal` enum + `composite_to_signal()` bucket
- `src/scoring/aggregator.py` — `ScoreCard`, `AnalysisReport` dataclasses + `ScoreAggregator`
- `src/scoring/indicators.py` — `IndicatorEngine` + `IndicatorSet` dataclass
- `src/scoring/strategy_runner.py` — Pydantic YAML schema + asteval rule evaluator + `StrategyRunner`
- `src/core/llm_explainer.py` — refactor phần LLM narrative ra module riêng
- `tests/test_signals.py`
- `tests/test_aggregator.py`
- `tests/test_indicators.py`
- `tests/test_strategy_runner.py`
- `tests/test_llm_explainer.py`
- `tests/test_analyzer_scoring.py`
- `tests/fixtures/__init__.py`
- `tests/fixtures/ohlcv_bullish.csv`
- `tests/fixtures/ohlcv_bearish.csv`
- `tests/fixtures/ohlcv_sideways.csv`

**Sửa:**
- `requirements.txt` — thêm `asteval`, `pandas-ta`
- `src/strategies/ma_crossover.yaml` — schema mới (weight/enabled/rules)
- `src/strategies/rsi_divergence.yaml`
- `src/strategies/volume_breakout.yaml`
- `src/strategies/support_resistance.yaml`
- `src/strategies/bollinger_bands.yaml`
- `src/strategies/vn30_momentum.yaml`
- `src/core/analyzer.py` — wire pipeline mới, trả `AnalysisReport`
- `src/notifier/telegram_bot.py` — render bảng điểm (adapter dict → report)
- `src/notifier/discord_bot.py` — render bảng điểm (adapter dict → report)
- `main.py` — print format mới
- `tests/test_analyzer.py` — cập nhật assertion sang `AnalysisReport`

---

## Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Thêm asteval và pandas-ta**

Mở `requirements.txt`, thêm 2 dòng:

```
asteval>=0.9.31
pandas-ta>=0.3.14b0
```

File cuối có các dòng mới ở cuối (sau `discord.py>=2.3.0`):

```
vnstock>=3.5.0
litellm>=1.20.0
fastapi>=0.100.0
uvicorn>=0.23.0
pytest>=7.0.0
python-dotenv>=1.0.0
pandas>=2.0.0
tenacity>=8.2.0
requests>=2.31.0
flake8>=6.0.0
pydantic>=2.0.0
APScheduler>=3.10.0
tqdm>=4.66.0
pyyaml>=6.0.1
jinja2>=3.1.2
python-telegram-bot>=20.0
discord.py>=2.3.0
asteval>=0.9.31
pandas-ta>=0.3.14b0
```

- [ ] **Step 2: Cài đặt**

Run: `pip install -r requirements.txt`
Expected: 2 packages mới được cài, không lỗi.

- [ ] **Step 3: Verify import**

Run: `python -c "import asteval, pandas_ta; print('ok')"`
Expected: in ra `ok`.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add asteval and pandas-ta for scoring engine"
```

---

## Task 2: Signal enum + composite bucket

**Files:**
- Create: `src/scoring/__init__.py`
- Create: `src/scoring/signals.py`
- Create: `tests/test_signals.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/test_signals.py`:

```python
"""Unit tests for Signal enum + composite_to_signal bucket."""
import pytest
from src.scoring.signals import Signal, composite_to_signal


class TestSignalEnum:
    def test_has_all_granular_values(self):
        expected = {
            "STRONG_BUY", "BUY", "BUY_WEAK",
            "NEUTRAL",
            "SELL_WEAK", "SELL", "STRONG_SELL",
        }
        assert {s.name for s in Signal} == expected

    def test_values_are_strings(self):
        assert Signal.BUY.value == "BUY"


class TestCompositeToSignal:
    @pytest.mark.parametrize("score,expected", [
        (0, Signal.STRONG_SELL),
        (19, Signal.STRONG_SELL),
        (20, Signal.SELL),
        (39, Signal.SELL),
        (40, Signal.NEUTRAL),
        (64, Signal.NEUTRAL),
        (65, Signal.BUY),
        (79, Signal.BUY),
        (80, Signal.STRONG_BUY),
        (100, Signal.STRONG_BUY),
    ])
    def test_boundaries(self, score, expected):
        assert composite_to_signal(score) is expected

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            composite_to_signal(-1)
        with pytest.raises(ValueError):
            composite_to_signal(101)

    def test_accepts_float(self):
        assert composite_to_signal(72.5) is Signal.BUY
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_signals.py -v`
Expected: `ModuleNotFoundError: No module named 'src.scoring'`

- [ ] **Step 3: Tạo package marker**

Tạo `src/scoring/__init__.py` (rỗng):

```python
"""Scoring engine: indicator computation, strategy evaluation, aggregation."""
```

- [ ] **Step 4: Implement signals.py**

Tạo `src/scoring/signals.py`:

```python
"""Signal enum used by strategies and the final aggregated report."""
from enum import Enum


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    BUY_WEAK = "BUY_WEAK"
    NEUTRAL = "NEUTRAL"
    SELL_WEAK = "SELL_WEAK"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


def composite_to_signal(score: float) -> Signal:
    """Map composite score 0-100 to the 5-level final signal bucket.

    80-100 → STRONG_BUY
    65-79  → BUY
    40-64  → NEUTRAL
    20-39  → SELL
    0-19   → STRONG_SELL
    """
    if score < 0 or score > 100:
        raise ValueError(f"score must be in [0, 100], got {score}")
    if score >= 80:
        return Signal.STRONG_BUY
    if score >= 65:
        return Signal.BUY
    if score >= 40:
        return Signal.NEUTRAL
    if score >= 20:
        return Signal.SELL
    return Signal.STRONG_SELL
```

- [ ] **Step 5: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_signals.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/scoring/__init__.py src/scoring/signals.py tests/test_signals.py
git commit -m "feat(scoring): add Signal enum and composite bucket"
```

---

## Task 3: ScoreCard + AnalysisReport + ScoreAggregator

**Files:**
- Create: `src/scoring/aggregator.py`
- Create: `tests/test_aggregator.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/test_aggregator.py`:

```python
"""Unit tests for ScoreCard, AnalysisReport, ScoreAggregator."""
import pytest
from src.scoring.signals import Signal
from src.scoring.aggregator import ScoreCard, AnalysisReport, ScoreAggregator


def card(name, score, weight=1.0, signal=Signal.NEUTRAL, reason="r", rule_matched=0):
    return ScoreCard(
        strategy_name=name, score=score, signal=signal,
        reason=reason, weight=weight, rule_matched=rule_matched,
    )


class TestScoreAggregator:
    def setup_method(self):
        self.agg = ScoreAggregator()

    def test_empty_cards_raises(self):
        with pytest.raises(ValueError):
            self.agg.aggregate([])

    def test_single_card_composite_equals_score(self):
        r = self.agg.aggregate([card("A", 72, weight=1.0)])
        assert r.composite == 72
        assert r.final_signal is Signal.BUY

    def test_equal_weights_is_mean(self):
        cards = [card("A", 80, 1.0), card("B", 60, 1.0), card("C", 40, 1.0)]
        r = self.agg.aggregate(cards)
        assert r.composite == pytest.approx(60.0)
        assert r.final_signal is Signal.NEUTRAL

    def test_weighted_average(self):
        # 90*2 + 50*1 = 230; weights=3; composite ≈ 76.67 → BUY
        cards = [card("A", 90, 2.0), card("B", 50, 1.0)]
        r = self.agg.aggregate(cards)
        assert r.composite == pytest.approx(230 / 3)
        assert r.final_signal is Signal.BUY

    def test_zero_weight_is_rejected(self):
        with pytest.raises(ValueError):
            self.agg.aggregate([card("A", 50, weight=0.0)])

    def test_report_preserves_cards(self):
        cards = [card("A", 80), card("B", 40)]
        r = self.agg.aggregate(cards)
        assert len(r.cards) == 2
        assert r.cards[0].strategy_name == "A"

    def test_composite_clamped_to_int_0_100(self):
        r = self.agg.aggregate([card("A", 100)])
        assert 0 <= r.composite <= 100


class TestAnalysisReport:
    def test_has_optional_narrative(self):
        r = AnalysisReport(composite=70, final_signal=Signal.BUY, cards=[])
        assert r.narrative is None
        r.narrative = "LLM text"
        assert r.narrative == "LLM text"
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_aggregator.py -v`
Expected: `ImportError` for `src.scoring.aggregator`.

- [ ] **Step 3: Implement aggregator.py**

Tạo `src/scoring/aggregator.py`:

```python
"""Aggregation of per-strategy ScoreCards into a composite AnalysisReport."""
from dataclasses import dataclass, field
from typing import List, Optional
from src.scoring.signals import Signal, composite_to_signal


@dataclass
class ScoreCard:
    strategy_name: str
    score: int
    signal: Signal
    reason: str
    weight: float
    rule_matched: int


@dataclass
class AnalysisReport:
    composite: float
    final_signal: Signal
    cards: List[ScoreCard] = field(default_factory=list)
    narrative: Optional[str] = None
    # Optional data carried through for notifier/main.py rendering
    symbol: Optional[str] = None
    info: Optional[dict] = None
    quote: Optional[dict] = None
    circuit_breaker: Optional[dict] = None


class ScoreAggregator:
    def aggregate(self, cards: List[ScoreCard]) -> AnalysisReport:
        if not cards:
            raise ValueError("Cannot aggregate empty cards list")
        total_weight = sum(c.weight for c in cards)
        if total_weight <= 0:
            raise ValueError("Total weight must be > 0")
        composite = sum(c.score * c.weight for c in cards) / total_weight
        composite = max(0.0, min(100.0, composite))
        return AnalysisReport(
            composite=composite,
            final_signal=composite_to_signal(composite),
            cards=list(cards),
        )
```

- [ ] **Step 4: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_aggregator.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scoring/aggregator.py tests/test_aggregator.py
git commit -m "feat(scoring): add ScoreCard, AnalysisReport, ScoreAggregator"
```

---

## Task 4: OHLCV Fixtures (3 scenarios)

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/ohlcv_bullish.csv`
- Create: `tests/fixtures/ohlcv_bearish.csv`
- Create: `tests/fixtures/ohlcv_sideways.csv`
- Create: `tests/fixtures/generate.py` (helper để tái tạo nếu cần)

- [ ] **Step 1: Tạo fixtures/__init__.py rỗng**

Tạo `tests/fixtures/__init__.py`:

```python
```

- [ ] **Step 2: Viết script sinh fixture**

Tạo `tests/fixtures/generate.py`:

```python
"""Generate synthetic OHLCV CSV fixtures for 3 market scenarios.

Run: python tests/fixtures/generate.py
Outputs: ohlcv_bullish.csv, ohlcv_bearish.csv, ohlcv_sideways.csv
Each: 200 rows, columns = date, open, high, low, close, volume.
Prices in thousands VND (matching vnstock KBS convention).
"""
import os
from datetime import date, timedelta
import pandas as pd
import numpy as np


def _business_days(n: int, start: str = "2025-09-01") -> list:
    d = date.fromisoformat(start)
    days = []
    while len(days) < n:
        if d.weekday() < 5:  # Mon–Fri
            days.append(d.isoformat())
        d += timedelta(days=1)
    return days


def _ohlcv_from_close(dates, closes, vol_base=2_000_000, vol_noise=500_000, seed=42):
    rng = np.random.default_rng(seed)
    opens = closes * (1 + rng.normal(0, 0.003, len(closes)))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.005, len(closes))))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.005, len(closes))))
    vols = (vol_base + rng.normal(0, vol_noise, len(closes))).clip(min=100_000).astype(int)
    return pd.DataFrame({
        "date": dates, "open": opens.round(2), "high": highs.round(2),
        "low": lows.round(2), "close": closes.round(2), "volume": vols,
    })


def build_bullish(n=200, start_price=50.0, end_price=80.0, seed=1):
    rng = np.random.default_rng(seed)
    trend = np.linspace(start_price, end_price, n)
    noise = rng.normal(0, 0.6, n)
    closes = trend + noise
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def build_bearish(n=200, start_price=80.0, end_price=50.0, seed=2):
    rng = np.random.default_rng(seed)
    trend = np.linspace(start_price, end_price, n)
    noise = rng.normal(0, 0.6, n)
    closes = trend + noise
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def build_sideways(n=200, center=60.0, amplitude=2.0, seed=3):
    rng = np.random.default_rng(seed)
    closes = center + amplitude * np.sin(np.linspace(0, 6 * np.pi, n)) + rng.normal(0, 0.5, n)
    return _ohlcv_from_close(_business_days(n), closes, seed=seed)


def main():
    out_dir = os.path.dirname(__file__)
    build_bullish().to_csv(os.path.join(out_dir, "ohlcv_bullish.csv"), index=False)
    build_bearish().to_csv(os.path.join(out_dir, "ohlcv_bearish.csv"), index=False)
    build_sideways().to_csv(os.path.join(out_dir, "ohlcv_sideways.csv"), index=False)
    print("Generated 3 fixtures.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Sinh CSV**

Run: `python tests/fixtures/generate.py`
Expected: in `Generated 3 fixtures.` và 3 file CSV xuất hiện.

- [ ] **Step 4: Smoke check**

Run: `python -c "import pandas as pd; df=pd.read_csv('tests/fixtures/ohlcv_bullish.csv'); print(len(df), df['close'].iloc[0], df['close'].iloc[-1])"`
Expected: `200 ~50.xx ~80.xx` (start < end cho bullish).

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/__init__.py tests/fixtures/generate.py tests/fixtures/ohlcv_*.csv
git commit -m "test(scoring): add 3 OHLCV scenario fixtures"
```

---

## Task 5: IndicatorEngine + IndicatorSet

**Files:**
- Create: `src/scoring/indicators.py`
- Create: `tests/test_indicators.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/test_indicators.py`:

```python
"""Unit tests for IndicatorEngine."""
import os
import pytest
import pandas as pd
from src.scoring.indicators import IndicatorEngine, IndicatorSet, InsufficientDataError


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def bullish_df():
    return pd.read_csv(os.path.join(FIXTURE_DIR, "ohlcv_bullish.csv"))


@pytest.fixture
def engine():
    return IndicatorEngine()


class TestIndicatorEngine:
    def test_returns_indicator_set(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert isinstance(out, IndicatorSet)

    def test_ma_computed_and_prev_available(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.MA20 is not None
        assert out.prev_MA20 is not None
        assert out.MA50 is not None

    def test_bullish_ma20_above_ma50(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.MA20 > out.MA50, "bullish scenario: MA20 should be above MA50"

    def test_rsi_in_valid_range(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert 0 <= out.RSI14 <= 100

    def test_bollinger_order(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.BB_lower < out.BB_mid < out.BB_upper

    def test_volume_ratio_positive(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.volume_ratio > 0

    def test_support_below_resistance(self, engine, bullish_df):
        out = engine.compute(bullish_df)
        assert out.support_20 < out.resistance_20

    def test_insufficient_data_raises(self, engine):
        short_df = pd.DataFrame({
            "date": ["2026-01-01", "2026-01-02"],
            "open": [10, 10], "high": [11, 11],
            "low": [9, 9], "close": [10, 10], "volume": [1000, 1000],
        })
        with pytest.raises(InsufficientDataError):
            engine.compute(short_df)

    def test_bearish_ma20_below_ma50(self, engine):
        df = pd.read_csv(os.path.join(FIXTURE_DIR, "ohlcv_bearish.csv"))
        out = IndicatorEngine().compute(df)
        assert out.MA20 < out.MA50, "bearish scenario: MA20 should be below MA50"
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_indicators.py -v`
Expected: `ImportError: src.scoring.indicators`.

- [ ] **Step 3: Implement indicators.py**

Tạo `src/scoring/indicators.py`:

```python
"""Centralized indicator computation. Returns an IndicatorSet snapshot."""
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import pandas_ta as ta


class InsufficientDataError(ValueError):
    """Raised when OHLCV data has too few rows for the indicators we need."""


@dataclass
class IndicatorSet:
    # Price
    close: float
    prev_close: float
    # Moving averages (SMA)
    MA5: Optional[float]
    MA10: Optional[float]
    MA20: Optional[float]
    MA50: Optional[float]
    MA200: Optional[float]
    prev_MA5: Optional[float]
    prev_MA20: Optional[float]
    prev_MA50: Optional[float]
    # Momentum
    RSI14: Optional[float]
    prev_RSI14: Optional[float]
    MACD: Optional[float]
    MACD_signal: Optional[float]
    MACD_hist: Optional[float]
    prev_MACD_hist: Optional[float]
    # Volatility
    BB_upper: Optional[float]
    BB_mid: Optional[float]
    BB_lower: Optional[float]
    ATR14: Optional[float]
    # Volume
    volume: float
    volume_ma20: Optional[float]
    volume_ratio: Optional[float]
    # Price structure
    support_20: Optional[float]
    resistance_20: Optional[float]


class IndicatorEngine:
    MIN_ROWS = 50  # enough for MA50 + comparison to previous row

    def compute(self, df: pd.DataFrame) -> IndicatorSet:
        if len(df) < self.MIN_ROWS:
            raise InsufficientDataError(
                f"Need at least {self.MIN_ROWS} rows, got {len(df)}"
            )

        df = df.copy().reset_index(drop=True)
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean() if len(df) >= 200 else pd.Series([None] * len(df))

        rsi = ta.rsi(close, length=14)

        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        # pandas-ta columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd = macd_df.iloc[:, 0] if macd_df is not None else pd.Series([None] * len(df))
        macd_hist = macd_df.iloc[:, 1] if macd_df is not None else pd.Series([None] * len(df))
        macd_signal = macd_df.iloc[:, 2] if macd_df is not None else pd.Series([None] * len(df))

        bb = ta.bbands(close, length=20, std=2)
        # pandas-ta columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, ...
        bb_lower = bb.iloc[:, 0] if bb is not None else pd.Series([None] * len(df))
        bb_mid = bb.iloc[:, 1] if bb is not None else pd.Series([None] * len(df))
        bb_upper = bb.iloc[:, 2] if bb is not None else pd.Series([None] * len(df))

        atr = ta.atr(df["high"].astype(float), df["low"].astype(float), close, length=14)

        vol_ma20 = volume.rolling(20).mean()

        last = len(df) - 1
        prev = last - 1

        last_ma20 = _val(ma20, last)
        last_vol_ma20 = _val(vol_ma20, last)

        return IndicatorSet(
            close=float(close.iloc[last]),
            prev_close=float(close.iloc[prev]),
            MA5=_val(ma5, last),
            MA10=_val(ma10, last),
            MA20=last_ma20,
            MA50=_val(ma50, last),
            MA200=_val(ma200, last) if ma200 is not None else None,
            prev_MA5=_val(ma5, prev),
            prev_MA20=_val(ma20, prev),
            prev_MA50=_val(ma50, prev),
            RSI14=_val(rsi, last),
            prev_RSI14=_val(rsi, prev),
            MACD=_val(macd, last),
            MACD_signal=_val(macd_signal, last),
            MACD_hist=_val(macd_hist, last),
            prev_MACD_hist=_val(macd_hist, prev),
            BB_upper=_val(bb_upper, last),
            BB_mid=_val(bb_mid, last),
            BB_lower=_val(bb_lower, last),
            ATR14=_val(atr, last),
            volume=float(volume.iloc[last]),
            volume_ma20=last_vol_ma20,
            volume_ratio=(float(volume.iloc[last]) / last_vol_ma20) if last_vol_ma20 else None,
            support_20=float(close.tail(20).min()),
            resistance_20=float(close.tail(20).max()),
        )


def _val(series, idx):
    """Return float(series[idx]) or None if NaN / out of range."""
    if series is None or idx < 0 or idx >= len(series):
        return None
    v = series.iloc[idx] if hasattr(series, "iloc") else series[idx]
    if v is None or pd.isna(v):
        return None
    return float(v)
```

- [ ] **Step 4: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_indicators.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scoring/indicators.py tests/test_indicators.py
git commit -m "feat(scoring): add IndicatorEngine with pandas-ta"
```

---

## Task 6: Strategy YAML Schema (Pydantic)

**Files:**
- Create: `src/scoring/strategy_runner.py` (partial — only schema in this task)
- Create: `tests/test_strategy_runner.py` (partial — schema tests)

- [ ] **Step 1: Viết failing test cho schema**

Tạo `tests/test_strategy_runner.py`:

```python
"""Unit tests for StrategyRunner schema, rule evaluator, and load_dir."""
import pytest
from pydantic import ValidationError
from src.scoring.strategy_runner import StrategyConfig


VALID_YAML = {
    "name": "MA Crossover",
    "weight": 1.0,
    "enabled": True,
    "indicators_required": ["MA20", "MA50"],
    "rules": [
        {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "uptrend"},
        {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fallback"},
    ],
}


class TestStrategyConfigSchema:
    def test_valid_config_loads(self):
        cfg = StrategyConfig(**VALID_YAML)
        assert cfg.name == "MA Crossover"
        assert cfg.weight == 1.0
        assert len(cfg.rules) == 2

    def test_name_required(self):
        bad = {**VALID_YAML}
        del bad["name"]
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_weight_must_be_positive(self):
        bad = {**VALID_YAML, "weight": 0}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_score_out_of_range_rejected(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 150, "signal": "BUY", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_rules_require_default_at_end(self):
        # Missing default rule
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_default_must_be_last_rule(self):
        bad = {**VALID_YAML, "rules": [
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_exactly_one_default(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BUY", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb1"},
            {"default": True, "score": 50, "signal": "NEUTRAL", "reason": "fb2"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)

    def test_invalid_signal_rejected(self):
        bad = {**VALID_YAML, "rules": [
            {"when": "MA20 > MA50", "score": 65, "signal": "BANANA", "reason": "x"},
            {"default": True, "score": 40, "signal": "NEUTRAL", "reason": "fb"},
        ]}
        with pytest.raises(ValidationError):
            StrategyConfig(**bad)
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py -v`
Expected: `ImportError: StrategyConfig`.

- [ ] **Step 3: Implement schema**

Tạo `src/scoring/strategy_runner.py`:

```python
"""YAML-driven strategy definition + safe rule evaluation."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from src.scoring.signals import Signal


class RuleConfig(BaseModel):
    when: Optional[str] = None
    default: bool = False
    score: int = Field(ge=0, le=100)
    signal: Signal
    reason: str

    @model_validator(mode="after")
    def _xor_when_default(self):
        if self.default and self.when:
            raise ValueError("Rule cannot have both `default` and `when`")
        if not self.default and not self.when:
            raise ValueError("Rule must have either `when` or `default: true`")
        return self


class StrategyConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    weight: float = Field(gt=0)
    enabled: bool = True
    indicators_required: List[str] = Field(default_factory=list)
    rules: List[RuleConfig] = Field(min_length=1)

    @field_validator("rules")
    @classmethod
    def _validate_rules(cls, rules: List[RuleConfig]) -> List[RuleConfig]:
        defaults = [i for i, r in enumerate(rules) if r.default]
        if len(defaults) != 1:
            raise ValueError(
                f"Exactly one rule must have `default: true`, got {len(defaults)}"
            )
        if defaults[0] != len(rules) - 1:
            raise ValueError("Default rule must be the LAST rule")
        return rules
```

- [ ] **Step 4: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scoring/strategy_runner.py tests/test_strategy_runner.py
git commit -m "feat(scoring): add Pydantic schema for strategy YAML"
```

---

## Task 7: Safe Rule Evaluator (asteval)

**Files:**
- Modify: `src/scoring/strategy_runner.py`
- Modify: `tests/test_strategy_runner.py`

- [ ] **Step 1: Viết failing test cho evaluator**

Thêm vào cuối `tests/test_strategy_runner.py`:

```python
from src.scoring.strategy_runner import RuleEvaluator


class TestRuleEvaluator:
    def setup_method(self):
        self.ev = RuleEvaluator()

    def test_simple_expression_true(self):
        assert self.ev.eval("a > b", {"a": 2, "b": 1}) is True

    def test_simple_expression_false(self):
        assert self.ev.eval("a > b", {"a": 1, "b": 2}) is False

    def test_compound_and(self):
        ctx = {"MA20": 10, "MA50": 8, "prev_MA20": 7, "prev_MA50": 8}
        assert self.ev.eval("MA20 > MA50 and prev_MA20 <= prev_MA50", ctx) is True

    def test_missing_variable_returns_false(self):
        # Rule referring to missing indicator -> skip (False)
        assert self.ev.eval("missing > 0", {"a": 1}) is False

    def test_none_value_returns_false(self):
        # If an indicator is None (NaN), comparisons skip
        assert self.ev.eval("x > 0", {"x": None}) is False

    def test_injection_import_blocked(self):
        with pytest.raises(ValueError):
            self.ev.eval("__import__('os').system('echo hi')", {})

    def test_injection_builtin_blocked(self):
        with pytest.raises(ValueError):
            self.ev.eval("open('/etc/passwd').read()", {})
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py::TestRuleEvaluator -v`
Expected: `ImportError: RuleEvaluator`.

- [ ] **Step 3: Implement RuleEvaluator**

Thêm vào `src/scoring/strategy_runner.py` (ngay dưới class `StrategyConfig`):

```python
from asteval import Interpreter


class RuleEvaluator:
    """Evaluate a boolean rule expression against a variable context.

    - Uses asteval (restricted AST). No imports, no builtins like open().
    - Missing or None variables cause the expression to return False (skip rule).
    - Any syntax error or attempt to access a dangerous name raises ValueError.
    """

    # asteval's default interpreter already strips __import__, exec, eval,
    # open, and similar. We still guard by checking the source text.
    _BLOCKED_TOKENS = ("__", "import", "open(", "exec(", "eval(", "compile(")

    def eval(self, expr: str, context: dict) -> bool:
        for tok in self._BLOCKED_TOKENS:
            if tok in expr:
                raise ValueError(f"Expression contains blocked token: {tok!r}")

        interp = Interpreter(no_print=True, minimal=True)
        # Reject None-valued or missing variables by short-circuiting to False
        safe_ctx = {k: v for k, v in context.items() if v is not None}
        for k, v in safe_ctx.items():
            interp.symtable[k] = v

        try:
            result = interp(expr)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expr!r}: {e}")

        if interp.error:
            # asteval accumulates errors in .error; a NameError for missing
            # variables should yield False (skip), not raise.
            first = interp.error[0]
            msg = str(first.get_error())
            if "not defined" in msg or "NameError" in msg:
                return False
            raise ValueError(f"Eval error for {expr!r}: {msg}")

        return bool(result)
```

- [ ] **Step 4: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py::TestRuleEvaluator -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scoring/strategy_runner.py tests/test_strategy_runner.py
git commit -m "feat(scoring): add safe asteval-based rule evaluator"
```

---

## Task 8: StrategyRunner (load_dir + run)

**Files:**
- Modify: `src/scoring/strategy_runner.py`
- Modify: `tests/test_strategy_runner.py`

- [ ] **Step 1: Viết failing test cho runner**

Thêm vào cuối `tests/test_strategy_runner.py`:

```python
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreCard


def _make_indicator_ctx(**overrides):
    base = {
        "close": 60.0, "prev_close": 59.5,
        "MA5": 60.2, "MA10": 60.0, "MA20": 59.8, "MA50": 59.0, "MA200": None,
        "prev_MA5": 60.0, "prev_MA20": 59.9, "prev_MA50": 59.1,
        "RSI14": 58.0, "prev_RSI14": 55.0,
        "MACD": 0.2, "MACD_signal": 0.1, "MACD_hist": 0.1, "prev_MACD_hist": 0.05,
        "BB_upper": 62.0, "BB_mid": 60.0, "BB_lower": 58.0, "ATR14": 1.1,
        "volume": 2_000_000, "volume_ma20": 1_500_000, "volume_ratio": 1.33,
        "support_20": 58.5, "resistance_20": 61.5,
    }
    base.update(overrides)
    return base


class TestStrategyRunner:
    def test_loads_valid_strategy_from_dict(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        cards = runner.run(_make_indicator_ctx())
        assert len(cards) == 1
        assert isinstance(cards[0], ScoreCard)

    def test_matches_first_rule(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        # MA20 > MA50 -> should match first rule with score 65
        cards = runner.run(_make_indicator_ctx(MA20=60, MA50=55))
        assert cards[0].score == 65
        assert cards[0].signal is Signal.BUY
        assert cards[0].rule_matched == 0

    def test_falls_through_to_default(self):
        runner = StrategyRunner([StrategyConfig(**VALID_YAML)])
        cards = runner.run(_make_indicator_ctx(MA20=55, MA50=60))
        assert cards[0].score == 40
        assert cards[0].signal is Signal.NEUTRAL
        assert cards[0].rule_matched == 1

    def test_disabled_strategy_skipped(self):
        cfg = StrategyConfig(**{**VALID_YAML, "enabled": False})
        runner = StrategyRunner([cfg])
        assert runner.run(_make_indicator_ctx()) == []

    def test_missing_required_indicator_skips(self):
        cfg = StrategyConfig(**{**VALID_YAML, "indicators_required": ["nonexistent"]})
        runner = StrategyRunner([cfg])
        assert runner.run(_make_indicator_ctx()) == []

    def test_load_dir_reads_yaml_files(self, tmp_path):
        yaml_content = """
name: "T1"
weight: 1.0
enabled: true
rules:
  - when: "close > 0"
    score: 70
    signal: BUY
    reason: "positive price"
  - default: true
    score: 40
    signal: NEUTRAL
    reason: "fallback"
"""
        (tmp_path / "t1.yaml").write_text(yaml_content, encoding="utf-8")
        runner = StrategyRunner.load_dir(str(tmp_path))
        assert len(runner.strategies) == 1
        cards = runner.run(_make_indicator_ctx())
        assert cards[0].score == 70
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py::TestStrategyRunner -v`
Expected: `ImportError: StrategyRunner`.

- [ ] **Step 3: Implement StrategyRunner**

Thêm import và class vào `src/scoring/strategy_runner.py` (bên dưới `RuleEvaluator`):

```python
import os
import glob
import yaml
from dataclasses import asdict, is_dataclass
from src.scoring.aggregator import ScoreCard


class StrategyRunner:
    def __init__(self, strategies: List[StrategyConfig]):
        self.strategies = strategies
        self.evaluator = RuleEvaluator()

    @classmethod
    def load_dir(cls, directory: str) -> "StrategyRunner":
        """Load *.yaml from directory, validate, return runner."""
        paths = sorted(glob.glob(os.path.join(directory, "*.yaml")))
        strategies: List[StrategyConfig] = []
        for p in paths:
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            strategies.append(StrategyConfig(**data))
        return cls(strategies)

    def run(self, context) -> List[ScoreCard]:
        """Evaluate all enabled strategies against the indicator context.

        `context` may be an IndicatorSet dataclass or a plain dict.
        """
        ctx = _as_dict(context)
        cards: List[ScoreCard] = []
        for cfg in self.strategies:
            if not cfg.enabled:
                continue
            if any(ctx.get(i) is None for i in cfg.indicators_required):
                continue
            card = self._evaluate_one(cfg, ctx)
            if card is not None:
                cards.append(card)
        return cards

    def _evaluate_one(self, cfg: StrategyConfig, ctx: dict) -> Optional[ScoreCard]:
        for idx, rule in enumerate(cfg.rules):
            if rule.default:
                matched = True
            else:
                matched = self.evaluator.eval(rule.when, ctx)
            if matched:
                return ScoreCard(
                    strategy_name=cfg.name,
                    score=rule.score,
                    signal=rule.signal,
                    reason=rule.reason,
                    weight=cfg.weight,
                    rule_matched=idx,
                )
        return None  # unreachable if default rule present


def _as_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Unsupported context type: {type(obj)}")
```

- [ ] **Step 4: Run tests, verify pass**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/scoring/strategy_runner.py tests/test_strategy_runner.py
git commit -m "feat(scoring): add StrategyRunner with YAML directory loading"
```

---

## Task 9: Migrate 6 YAML Strategies to New Schema

**Files:**
- Modify: `src/strategies/ma_crossover.yaml`
- Modify: `src/strategies/rsi_divergence.yaml`
- Modify: `src/strategies/volume_breakout.yaml`
- Modify: `src/strategies/support_resistance.yaml`
- Modify: `src/strategies/bollinger_bands.yaml`
- Modify: `src/strategies/vn30_momentum.yaml`
- Modify: `tests/test_strategy_runner.py` (add load-real-dir test)

- [ ] **Step 1: Viết test load-real-dir**

Thêm vào cuối `tests/test_strategy_runner.py`:

```python
import os as _os


class TestRealStrategyYAMLs:
    STRATEGY_DIR = _os.path.join(_os.path.dirname(__file__), "..", "src", "strategies")

    def test_all_yamls_load_cleanly(self):
        runner = StrategyRunner.load_dir(self.STRATEGY_DIR)
        assert len(runner.strategies) == 6
        names = {s.name for s in runner.strategies}
        assert "MA Crossover" in names

    def test_runs_against_bullish_fixture(self):
        import pandas as pd
        from src.scoring.indicators import IndicatorEngine
        df = pd.read_csv(_os.path.join(_os.path.dirname(__file__), "fixtures", "ohlcv_bullish.csv"))
        ind = IndicatorEngine().compute(df)
        runner = StrategyRunner.load_dir(self.STRATEGY_DIR)
        cards = runner.run(ind)
        assert len(cards) >= 1, "at least one strategy should produce a card"
        # Most strategies should lean BUY in bullish fixture
        buy_like = sum(1 for c in cards if c.signal in (Signal.BUY, Signal.BUY_WEAK, Signal.STRONG_BUY))
        assert buy_like >= len(cards) // 2
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py::TestRealStrategyYAMLs -v`
Expected: FAIL (YAMLs still use old schema).

- [ ] **Step 3: Rewrite `ma_crossover.yaml`**

Overwrite `src/strategies/ma_crossover.yaml`:

```yaml
name: "MA Crossover"
description: "Đường MA ngắn hạn (MA20) cắt MA dài hạn (MA50)."
weight: 1.0
enabled: true
indicators_required: [MA20, MA50, prev_MA20, prev_MA50]
rules:
  - when: "MA20 > MA50 and prev_MA20 <= prev_MA50"
    score: 85
    signal: BUY
    reason: "Golden cross: MA20 vừa cắt lên MA50"
  - when: "MA20 > MA50"
    score: 65
    signal: BUY_WEAK
    reason: "MA20 trên MA50 — xu hướng tăng ngắn hạn"
  - when: "MA20 < MA50 and prev_MA20 >= prev_MA50"
    score: 15
    signal: SELL
    reason: "Death cross: MA20 vừa cắt xuống MA50"
  - default: true
    score: 40
    signal: NEUTRAL
    reason: "MA20 dưới MA50 — xu hướng giảm"
```

- [ ] **Step 4: Rewrite `rsi_divergence.yaml`**

Overwrite `src/strategies/rsi_divergence.yaml`:

```yaml
name: "RSI Momentum"
description: "Dựa trên RSI14 — quá bán, quá mua, và đà hồi phục."
weight: 1.0
enabled: true
indicators_required: [RSI14, prev_RSI14]
rules:
  - when: "RSI14 < 30 and RSI14 > prev_RSI14"
    score: 80
    signal: BUY
    reason: "RSI thoát vùng quá bán — tín hiệu hồi phục"
  - when: "RSI14 < 30"
    score: 55
    signal: NEUTRAL
    reason: "RSI ở vùng quá bán, chờ xác nhận"
  - when: "RSI14 > 70 and RSI14 < prev_RSI14"
    score: 20
    signal: SELL
    reason: "RSI rời vùng quá mua — rủi ro điều chỉnh"
  - when: "RSI14 > 70"
    score: 45
    signal: NEUTRAL
    reason: "RSI quá mua nhưng đà tăng chưa gãy"
  - when: "RSI14 >= 50"
    score: 60
    signal: BUY_WEAK
    reason: "RSI trên 50 — bias tăng"
  - default: true
    score: 40
    signal: NEUTRAL
    reason: "RSI dưới 50, bias giảm"
```

- [ ] **Step 5: Rewrite `volume_breakout.yaml`**

Overwrite `src/strategies/volume_breakout.yaml`:

```yaml
name: "Volume Breakout"
description: "Khối lượng đột biến xác nhận chuyển động giá."
weight: 1.0
enabled: true
indicators_required: [volume_ratio, close, prev_close]
rules:
  - when: "volume_ratio >= 2.0 and close > prev_close"
    score: 85
    signal: BUY
    reason: "KL 2x+ trung bình kèm giá tăng — breakout xác nhận"
  - when: "volume_ratio >= 1.5 and close > prev_close"
    score: 70
    signal: BUY
    reason: "KL cao kèm giá tăng — đà mua mạnh"
  - when: "volume_ratio >= 2.0 and close < prev_close"
    score: 15
    signal: SELL
    reason: "KL đột biến kèm giá giảm — áp lực bán"
  - when: "volume_ratio < 0.5"
    score: 40
    signal: NEUTRAL
    reason: "KL thấp — thị trường thiếu quan tâm"
  - default: true
    score: 50
    signal: NEUTRAL
    reason: "KL bình thường, không có tín hiệu breakout"
```

- [ ] **Step 6: Rewrite `support_resistance.yaml`**

Overwrite `src/strategies/support_resistance.yaml`:

```yaml
name: "Support / Resistance"
description: "Vị trí giá so với hỗ trợ / kháng cự 20 phiên."
weight: 1.0
enabled: true
indicators_required: [close, support_20, resistance_20]
rules:
  - when: "close <= support_20 * 1.02"
    score: 75
    signal: BUY
    reason: "Giá gần hỗ trợ 20 phiên — vùng mua hấp dẫn"
  - when: "close >= resistance_20 * 0.98"
    score: 30
    signal: SELL_WEAK
    reason: "Giá gần kháng cự 20 phiên — rủi ro chốt lời"
  - when: "close > resistance_20"
    score: 80
    signal: BUY
    reason: "Giá vượt kháng cự 20 phiên — breakout"
  - default: true
    score: 50
    signal: NEUTRAL
    reason: "Giá trong biên hỗ trợ / kháng cự"
```

- [ ] **Step 7: Rewrite `bollinger_bands.yaml`**

Overwrite `src/strategies/bollinger_bands.yaml`:

```yaml
name: "Bollinger Bands"
description: "Vị trí giá so với Bollinger Band 20 phiên."
weight: 1.0
enabled: true
indicators_required: [close, BB_lower, BB_mid, BB_upper]
rules:
  - when: "close <= BB_lower"
    score: 75
    signal: BUY
    reason: "Giá chạm band dưới — khả năng hồi phục"
  - when: "close >= BB_upper"
    score: 25
    signal: SELL_WEAK
    reason: "Giá chạm band trên — rủi ro điều chỉnh"
  - when: "close > BB_mid"
    score: 60
    signal: BUY_WEAK
    reason: "Giá trên band giữa — bias tăng"
  - default: true
    score: 45
    signal: NEUTRAL
    reason: "Giá dưới band giữa — bias giảm"
```

- [ ] **Step 8: Rewrite `vn30_momentum.yaml`**

Overwrite `src/strategies/vn30_momentum.yaml`:

```yaml
name: "Price Momentum"
description: "Động lượng giá dựa trên MACD và thay đổi gần nhất."
weight: 1.0
enabled: true
indicators_required: [MACD_hist, prev_MACD_hist]
rules:
  - when: "MACD_hist > 0 and prev_MACD_hist <= 0"
    score: 80
    signal: BUY
    reason: "MACD histogram vừa chuyển dương — momentum tăng"
  - when: "MACD_hist > 0 and MACD_hist > prev_MACD_hist"
    score: 70
    signal: BUY
    reason: "Momentum tăng đang mở rộng"
  - when: "MACD_hist < 0 and prev_MACD_hist >= 0"
    score: 20
    signal: SELL
    reason: "MACD histogram vừa chuyển âm — momentum giảm"
  - when: "MACD_hist > 0"
    score: 60
    signal: BUY_WEAK
    reason: "Momentum dương nhưng đà thu hẹp"
  - default: true
    score: 40
    signal: NEUTRAL
    reason: "Momentum âm"
```

- [ ] **Step 9: Run tests**

Run: `PYTHONPATH=. pytest tests/test_strategy_runner.py -v`
Expected: all PASS (including `TestRealStrategyYAMLs`).

- [ ] **Step 10: Commit**

```bash
git add src/strategies/*.yaml tests/test_strategy_runner.py
git commit -m "feat(strategies): migrate 6 YAMLs to scoring schema"
```

---

## Task 10: LLMExplainer (narrative only, no scoring)

**Files:**
- Create: `src/core/llm_explainer.py`
- Create: `tests/test_llm_explainer.py`

- [ ] **Step 1: Viết failing test**

Tạo `tests/test_llm_explainer.py`:

```python
"""Unit tests for LLMExplainer — narrative generation given a filled AnalysisReport."""
from unittest.mock import MagicMock
from src.core.llm_explainer import LLMExplainer
from src.scoring.aggregator import ScoreCard, AnalysisReport
from src.scoring.signals import Signal


def _report():
    return AnalysisReport(
        composite=72.0,
        final_signal=Signal.BUY,
        cards=[
            ScoreCard("MA Crossover", 85, Signal.BUY, "Golden cross", 1.0, 0),
            ScoreCard("RSI Momentum", 55, Signal.NEUTRAL, "RSI 58", 1.0, 0),
        ],
        symbol="VNM.HO",
        info={"company_name": "Vinamilk", "industry": "Food", "exchange": "HOSE"},
        quote={"price": 61.3, "change_pct": 0.33, "volume": 3_100_000},
    )


class TestLLMExplainer:
    def test_returns_string_narrative(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Narrative text"
        exp = LLMExplainer(llm_client=mock_llm)
        text = exp.explain(_report())
        assert text == "Narrative text"
        mock_llm.generate.assert_called_once()

    def test_prompt_contains_scores_and_signal(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "ok"
        exp = LLMExplainer(llm_client=mock_llm)
        exp.explain(_report())
        prompt = mock_llm.generate.call_args[0][0]
        assert "72" in prompt  # composite
        assert "BUY" in prompt
        assert "MA Crossover" in prompt
        assert "VNM.HO" in prompt

    def test_prompt_forbids_changing_scores(self):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "ok"
        exp = LLMExplainer(llm_client=mock_llm)
        exp.explain(_report())
        prompt = mock_llm.generate.call_args[0][0]
        assert "KHÔNG" in prompt or "không được" in prompt.lower()
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_llm_explainer.py -v`
Expected: `ImportError: src.core.llm_explainer`.

- [ ] **Step 3: Implement LLMExplainer**

Tạo `src/core/llm_explainer.py`:

```python
"""LLMExplainer — generates a Vietnamese narrative given a filled AnalysisReport.

The LLM is NOT allowed to change scores or signals; it only explains them.
"""
from src.core.llm_client import LiteLLMClient
from src.scoring.aggregator import AnalysisReport


class LLMExplainer:
    def __init__(self, llm_client=None):
        self.llm = llm_client or LiteLLMClient()

    def explain(self, report: AnalysisReport) -> str:
        prompt = self._build_prompt(report)
        return self.llm.generate(prompt)

    def _build_prompt(self, r: AnalysisReport) -> str:
        info = r.info or {}
        quote = r.quote or {}
        lines = [
            "Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam.",
            "Hệ thống đã TÍNH SẴN điểm và tín hiệu cho từng chiến lược.",
            "",
            "NHIỆM VỤ DUY NHẤT: Giải thích kết quả bằng 3-5 câu tiếng Việt.",
            "",
            "TUYỆT ĐỐI KHÔNG:",
            "- Đổi điểm số",
            "- Đưa khuyến nghị trái ngược tín hiệu composite",
            "- Bịa thêm chỉ báo không có trong dữ liệu",
            "",
            f"Mã: {r.symbol or ''}",
            f"Công ty: {info.get('company_name', '')} | Ngành: {info.get('industry', 'N/A')} | Sàn: {info.get('exchange', '')}",
            f"Giá: {quote.get('price', 0):.2f} (x1000đ) | Thay đổi: {quote.get('change_pct', 0):+.2f}%",
            "",
            f"Composite Score: {r.composite:.0f}/100 → {r.final_signal.value}",
            "",
            "Bảng điểm từng chiến lược:",
        ]
        for c in r.cards:
            lines.append(
                f"- {c.strategy_name}: {c.score}/100 [{c.signal.value}] — {c.reason}"
            )
        lines.append("")
        lines.append("Hãy viết 3-5 câu diễn giải bằng tiếng Việt, nhấn mạnh mức độ đồng thuận giữa các chiến lược.")
        return "\n".join(lines)
```

- [ ] **Step 4: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_llm_explainer.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/llm_explainer.py tests/test_llm_explainer.py
git commit -m "feat(core): add LLMExplainer for narrative generation"
```

---

## Task 11: Refactor Analyzer to new pipeline

**Files:**
- Modify: `src/core/analyzer.py`
- Create: `tests/test_analyzer_scoring.py`
- Modify: `tests/test_analyzer.py` (update assertions)

- [ ] **Step 1: Viết failing integration test cho pipeline mới**

Tạo `tests/test_analyzer_scoring.py`:

```python
"""Integration tests: Analyzer end-to-end with fixture OHLCV scenarios."""
import os
import pandas as pd
import pytest
from unittest.mock import MagicMock
from src.core.analyzer import Analyzer
from src.scoring.aggregator import AnalysisReport
from src.scoring.signals import Signal


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _mock_analyzer(scenario: str):
    df = pd.read_csv(os.path.join(FIXTURE_DIR, f"ohlcv_{scenario}.csv"))
    analyzer = Analyzer()  # loads real strategies from src/strategies

    # Replace router with mock
    info = {"symbol": "TEST", "company_name": "Test Co", "industry": "X", "exchange": "HOSE"}
    last = df.iloc[-1]
    quote = {
        "symbol": "TEST", "price": float(last["close"]),
        "change": float(last["close"] - df.iloc[-2]["close"]),
        "change_pct": 0.5, "volume": float(last["volume"]),
        "open": float(last["open"]), "high": float(last["high"]), "low": float(last["low"]),
    }

    mock_router = MagicMock()
    mock_router.execute_with_fallback.side_effect = lambda method, *args: {
        "get_stock_info": info,
        "get_realtime_quote": quote,
        "get_historical_data": df,
    }[method]
    analyzer.router = mock_router

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Narrative placeholder."
    analyzer.explainer.llm = mock_llm

    return analyzer


class TestAnalyzerScoring:
    def test_returns_analysis_report(self):
        analyzer = _mock_analyzer("bullish")
        out = analyzer.analyze("TEST.HO")
        assert isinstance(out, AnalysisReport)

    def test_bullish_scenario_has_buy_lean(self):
        analyzer = _mock_analyzer("bullish")
        report = analyzer.analyze("TEST.HO")
        assert report.composite >= 55, f"bullish composite too low: {report.composite}"
        assert report.final_signal in (Signal.BUY, Signal.STRONG_BUY, Signal.NEUTRAL)

    def test_bearish_scenario_has_sell_lean(self):
        analyzer = _mock_analyzer("bearish")
        report = analyzer.analyze("TEST.HO")
        assert report.composite <= 55, f"bearish composite too high: {report.composite}"

    def test_cards_populated(self):
        analyzer = _mock_analyzer("bullish")
        report = analyzer.analyze("TEST.HO")
        assert len(report.cards) >= 4  # most strategies should produce cards

    def test_narrative_set(self):
        analyzer = _mock_analyzer("bullish")
        report = analyzer.analyze("TEST.HO")
        assert report.narrative == "Narrative placeholder."

    def test_info_and_quote_attached(self):
        analyzer = _mock_analyzer("bullish")
        report = analyzer.analyze("TEST.HO")
        assert report.info is not None
        assert report.quote is not None
        assert report.symbol and "TEST" in report.symbol
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_analyzer_scoring.py -v`
Expected: FAIL (Analyzer still returns dict).

- [ ] **Step 3: Refactor Analyzer**

Overwrite `src/core/analyzer.py`:

```python
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

from src.data_provider.vnstock_provider import VNStockProvider
from src.data_provider.fallback_router import FallbackRouter
from src.utils.validator import VNStockValidator
from src.market.circuit_breaker import CircuitBreakerHandler
from src.core.llm_explainer import LLMExplainer
from src.scoring.indicators import IndicatorEngine, InsufficientDataError
from src.scoring.strategy_runner import StrategyRunner
from src.scoring.aggregator import ScoreAggregator, AnalysisReport
from src.scoring.signals import Signal

logger = logging.getLogger(__name__)


class Analyzer:
    """Core orchestrator for per-stock analysis using the scoring engine."""

    def __init__(self, strategy_dir: str = "src/strategies"):
        self.router = FallbackRouter([VNStockProvider()])
        self.circuit_breaker = CircuitBreakerHandler()
        self.indicators = IndicatorEngine()
        self.strategy_runner = StrategyRunner.load_dir(strategy_dir)
        self.aggregator = ScoreAggregator()
        self.explainer = LLMExplainer()

    def analyze(self, symbol: str) -> Union[AnalysisReport, dict]:
        logger.info(f"Bắt đầu phân tích {symbol}")

        is_valid, msg = VNStockValidator.validate(symbol)
        if not is_valid:
            return {"symbol": symbol, "error": msg, "status": "failed"}
        normalized = VNStockValidator.normalize(symbol)

        try:
            info = self.router.execute_with_fallback("get_stock_info", normalized)
            quote = self.router.execute_with_fallback("get_realtime_quote", normalized)
            start = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
            end = datetime.today().strftime('%Y-%m-%d')
            df = self.router.execute_with_fallback(
                "get_historical_data", normalized, start, end,
            )

            cb_status = self._check_circuit_breaker(normalized, df, quote)

            try:
                ind = self.indicators.compute(df)
            except InsufficientDataError as e:
                logger.warning(f"Insufficient data for {normalized}: {e}")
                return {"symbol": normalized, "error": str(e), "status": "failed"}

            cards = self.strategy_runner.run(ind)
            if not cards:
                return {
                    "symbol": normalized,
                    "error": "Không có chiến lược nào áp dụng được (thiếu dữ liệu)",
                    "status": "failed",
                }

            report = self.aggregator.aggregate(cards)
            report.symbol = normalized
            report.info = info
            report.quote = quote
            report.circuit_breaker = cb_status

            try:
                report.narrative = self.explainer.explain(report)
            except Exception as e:
                logger.error(f"LLM explain failed: {e}")
                return {"symbol": normalized, "error": str(e), "status": "failed"}

            return report

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {"symbol": symbol, "error": str(e), "status": "failed"}

    def _check_circuit_breaker(self, symbol: str, df, quote) -> Optional[dict]:
        if df is None or df.empty or len(df) < 2 or 'close' not in df.columns:
            return None
        prev_close = float(df.iloc[-2]['close'])
        current = quote.get('price', 0)
        if prev_close <= 0 or current <= 0:
            return None
        self.circuit_breaker.set_reference_price(symbol, prev_close)
        return self.circuit_breaker.check_limit_status(symbol, current)
```

- [ ] **Step 4: Run the new integration test**

Run: `PYTHONPATH=. pytest tests/test_analyzer_scoring.py -v`
Expected: all PASS.

- [ ] **Step 5: Update `tests/test_analyzer.py`**

Old test expects dict with `tech_summary`, `llm_analysis` keys. Replace `tests/test_analyzer.py` entirely:

```python
"""Integration tests for Analyzer (core orchestrator).

Uses full mocks — no network, no LLM API calls.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock

from src.core.analyzer import Analyzer
from src.scoring.aggregator import AnalysisReport


@pytest.fixture
def mock_df():
    """200-day OHLCV for full indicator coverage."""
    import numpy as np
    rng = np.random.default_rng(0)
    closes = np.linspace(60.0, 65.0, 200) + rng.normal(0, 0.3, 200)
    return pd.DataFrame({
        'date': [f'2025-{(i % 12) + 1:02d}-01' for i in range(200)],
        'open': closes, 'high': closes + 1,
        'low': closes - 1, 'close': closes,
        'volume': [2_000_000 + i * 1000 for i in range(200)],
    })


@pytest.fixture
def mock_quote():
    return {
        "symbol": "VNM", "price": 65.0, "change": 0.2,
        "change_pct": 0.33, "volume": 3_115_500,
        "open": 64.8, "high": 65.5, "low": 64.7, "date": "2026-04-17",
    }


@pytest.fixture
def mock_info():
    return {
        "symbol": "VNM", "exchange": "HOSE",
        "company_name": "CTCP Sữa Việt Nam",
        "industry": "Thực phẩm", "website": "https://vinamilk.com.vn",
    }


@pytest.fixture
def analyzer_with_mocks(mock_df, mock_quote, mock_info):
    analyzer = Analyzer()
    mock_router = MagicMock()
    mock_router.execute_with_fallback.side_effect = lambda method, *args: {
        "get_stock_info": mock_info,
        "get_realtime_quote": mock_quote,
        "get_historical_data": mock_df,
    }[method]
    analyzer.router = mock_router

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "VNM có xu hướng tăng. Khuyến nghị GIỮ."
    analyzer.explainer.llm = mock_llm
    return analyzer


class TestAnalyzerValidation:
    def test_invalid_symbol_returns_failed(self):
        analyzer = Analyzer()
        result = analyzer.analyze("INVALID@SYMBOL")
        assert isinstance(result, dict)
        assert result['status'] == 'failed'

    def test_empty_symbol_returns_failed(self):
        analyzer = Analyzer()
        result = analyzer.analyze("")
        assert isinstance(result, dict)
        assert result['status'] == 'failed'


class TestAnalyzerSuccess:
    def test_returns_analysis_report(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert isinstance(result, AnalysisReport)

    def test_report_has_composite(self, analyzer_with_mocks):
        report = analyzer_with_mocks.analyze("VNM.HO")
        assert 0 <= report.composite <= 100

    def test_report_has_narrative(self, analyzer_with_mocks):
        report = analyzer_with_mocks.analyze("VNM.HO")
        assert report.narrative and len(report.narrative) > 0

    def test_report_has_cards(self, analyzer_with_mocks):
        report = analyzer_with_mocks.analyze("VNM.HO")
        assert len(report.cards) >= 1

    def test_info_attached(self, analyzer_with_mocks):
        report = analyzer_with_mocks.analyze("VNM.HO")
        assert report.info["company_name"] == "CTCP Sữa Việt Nam"


class TestAnalyzerErrorHandling:
    def test_data_provider_error_returns_failed(self):
        analyzer = Analyzer()
        mock_router = MagicMock()
        mock_router.execute_with_fallback.side_effect = RuntimeError("Network error")
        analyzer.router = mock_router
        result = analyzer.analyze("VNM.HO")
        assert isinstance(result, dict)
        assert result['status'] == 'failed'

    def test_llm_error_returns_failed(self, mock_df, mock_quote, mock_info):
        analyzer = Analyzer()
        mock_router = MagicMock()
        mock_router.execute_with_fallback.side_effect = lambda method, *args: {
            "get_stock_info": mock_info,
            "get_realtime_quote": mock_quote,
            "get_historical_data": mock_df,
        }[method]
        analyzer.router = mock_router
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("LLM timeout")
        analyzer.explainer.llm = mock_llm
        result = analyzer.analyze("VNM.HO")
        assert isinstance(result, dict)
        assert result['status'] == 'failed'
```

- [ ] **Step 6: Run full test suite**

Run: `PYTHONPATH=. pytest tests/ -v`
Expected: all PASS (existing tests still green, plus new ones).

- [ ] **Step 7: Commit**

```bash
git add src/core/analyzer.py tests/test_analyzer.py tests/test_analyzer_scoring.py
git commit -m "refactor(core): wire Analyzer through new scoring pipeline"
```

---

## Task 12: Notifier adapter (dict OR AnalysisReport)

**Files:**
- Modify: `src/notifier/telegram_bot.py`
- Modify: `src/notifier/discord_bot.py`
- Modify: `tests/test_notifier.py` (verify both paths)

- [ ] **Step 1: Viết failing test**

Mở `tests/test_notifier.py` để xem hiện trạng. Thêm test cases sau (append cuối file):

```python
from src.scoring.aggregator import AnalysisReport, ScoreCard
from src.scoring.signals import Signal
from src.notifier.telegram_bot import TelegramNotifier
from src.notifier.discord_bot import DiscordNotifier


def _sample_report():
    return AnalysisReport(
        composite=72.0,
        final_signal=Signal.BUY,
        cards=[
            ScoreCard("MA Crossover", 85, Signal.BUY, "Golden cross", 1.0, 0),
            ScoreCard("RSI Momentum", 55, Signal.NEUTRAL, "RSI 58", 1.0, 0),
        ],
        narrative="VNM có xu hướng tăng tích cực...",
        symbol="VNM.HO",
        info={"company_name": "Vinamilk", "industry": "Food", "exchange": "HOSE"},
        quote={"price": 61.3, "change_pct": 0.33, "volume": 3_100_000},
    )


class TestTelegramAnalysisReport:
    def test_format_report_contains_composite(self):
        n = TelegramNotifier()
        msg = n.format_message(_sample_report())
        assert "72" in msg
        assert "BUY" in msg
        assert "MA Crossover" in msg
        assert "VNM.HO" in msg

    def test_format_report_accepts_dict_legacy(self):
        n = TelegramNotifier()
        msg = n.format_message({
            "symbol": "X.HO", "info": {"company_name": "Co"},
            "quote": {"price": 10.0}, "llm_analysis": "legacy",
        })
        assert "X.HO" in msg


class TestDiscordAnalysisReport:
    def test_format_embed_has_score_fields(self):
        n = DiscordNotifier()
        embed = n.format_embed(_sample_report())
        # Embed must include composite score in title or description
        assert "72" in (embed.get("title", "") + embed.get("description", ""))
        # Cards should become fields
        field_names = [f["name"] for f in embed.get("fields", [])]
        assert any("MA Crossover" in n for n in field_names)

    def test_format_embed_accepts_dict_legacy(self):
        n = DiscordNotifier()
        embed = n.format_embed({
            "symbol": "X.HO", "info": {"company_name": "Co"},
            "quote": {"price": 10.0}, "llm_analysis": "legacy",
        })
        assert "X.HO" in embed.get("title", "")
```

- [ ] **Step 2: Run test, verify fail**

Run: `PYTHONPATH=. pytest tests/test_notifier.py::TestTelegramAnalysisReport tests/test_notifier.py::TestDiscordAnalysisReport -v`
Expected: `AttributeError: 'TelegramNotifier' object has no attribute 'format_message'`.

- [ ] **Step 3: Refactor TelegramNotifier**

Overwrite `src/notifier/telegram_bot.py`:

```python
import os
import requests
import logging
from typing import Any, Union
from .base import BaseNotifier
from src.scoring.aggregator import AnalysisReport

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Telegram notifier — supports AnalysisReport and legacy dict."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.is_configured = bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> bool:
        if not self.is_configured:
            logger.warning("Telegram Bot is not configured.")
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent message to Telegram successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_report(self, report: Union[AnalysisReport, dict]) -> bool:
        return self.send_message(self.format_message(report))

    def format_message(self, report: Union[AnalysisReport, dict]) -> str:
        if isinstance(report, AnalysisReport):
            return self._format_report(report)
        return self._format_legacy(report)

    def _format_report(self, r: AnalysisReport) -> str:
        info = r.info or {}
        quote = r.quote or {}
        lines = [
            f"📊 *VN STOCK REPORT: {r.symbol or ''}*",
            "",
            f"🏢 *{info.get('company_name', '')}* | {info.get('industry', 'N/A')} | {info.get('exchange', '')}",
            f"💰 *Giá*: {quote.get('price', 0) * 1000:,.0f}đ ({quote.get('change_pct', 0):+.2f}%)",
            "",
            f"🎯 *Composite: {r.composite:.0f}/100 → {r.final_signal.value}*",
            "",
            "*Bảng điểm:*",
        ]
        for c in r.cards:
            lines.append(f"• {c.strategy_name}: *{c.score}* [{c.signal.value}] — {c.reason}")
        if r.narrative:
            lines.append("")
            lines.append("🤖 *Phân tích:*")
            lines.append(r.narrative)
        lines.append("")
        lines.append("---")
        return "\n".join(lines)

    def _format_legacy(self, report_data: dict) -> str:
        symbol = report_data.get('symbol', 'Unknown')
        info = report_data.get('info', {})
        quote = report_data.get('quote', {})
        cb = report_data.get('circuit_breaker', {})
        llm = report_data.get('llm_analysis', 'No analysis')
        msg = f"📊 *VN STOCK REPORT: {symbol}*\n\n"
        msg += f"🏢 *Công ty*: {info.get('company_name')} | {info.get('industry')}\n"
        msg += f"💰 *Giá*: {quote.get('price', 0):,.0f} đ\n"
        if cb and cb.get('warning'):
            msg += f"⚠️ *Cảnh báo*: {cb.get('warning')}\n"
        msg += f"\n🤖 *Nhận định LLM*:\n{llm}\n\n---"
        return msg
```

- [ ] **Step 4: Refactor DiscordNotifier**

Overwrite `src/notifier/discord_bot.py`:

```python
import os
import requests
import logging
from typing import Union
from .base import BaseNotifier
from src.scoring.aggregator import AnalysisReport

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """Discord notifier — supports AnalysisReport and legacy dict."""

    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.is_configured = bool(self.webhook_url)

    def send_message(self, message: str) -> bool:
        if not self.is_configured:
            logger.warning("Discord Webhook is not configured.")
            return False
        try:
            response = requests.post(self.webhook_url, json={"content": message}, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False

    def send_report(self, report: Union[AnalysisReport, dict]) -> bool:
        if not self.is_configured:
            return False
        embed = self.format_embed(report)
        try:
            response = requests.post(self.webhook_url, json={"embeds": [embed]}, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord report: {e}")
            return False

    def format_embed(self, report: Union[AnalysisReport, dict]) -> dict:
        if isinstance(report, AnalysisReport):
            return self._format_report(report)
        return self._format_legacy(report)

    def _format_report(self, r: AnalysisReport) -> dict:
        info = r.info or {}
        quote = r.quote or {}
        color = self._color_for(r.final_signal.value)
        fields = [
            {
                "name": "🎯 Composite",
                "value": f"{r.composite:.0f}/100 → **{r.final_signal.value}**",
                "inline": False,
            },
            {
                "name": "💰 Giá",
                "value": f"{quote.get('price', 0) * 1000:,.0f}đ ({quote.get('change_pct', 0):+.2f}%)",
                "inline": True,
            },
            {
                "name": "🏢 Công ty",
                "value": f"{info.get('company_name', '')} | {info.get('industry', 'N/A')}",
                "inline": True,
            },
        ]
        for c in r.cards:
            fields.append({
                "name": f"{c.strategy_name}: {c.score}/100 [{c.signal.value}]",
                "value": c.reason,
                "inline": False,
            })
        return {
            "title": f"Báo Cáo: {r.symbol or ''}",
            "description": (r.narrative or "")[:4000],
            "color": color,
            "fields": fields,
        }

    def _format_legacy(self, report_data: dict) -> dict:
        symbol = report_data.get('symbol', 'Unknown')
        info = report_data.get('info', {})
        quote = report_data.get('quote', {})
        llm = report_data.get('llm_analysis', 'No analysis')
        return {
            "title": f"Báo Cáo Phân Tích Cổ Phiếu: {symbol}",
            "description": llm[:4000],
            "color": 3447003,
            "fields": [
                {"name": "🏢 Công ty",
                 "value": f"{info.get('company_name')} | {info.get('industry')}",
                 "inline": False},
                {"name": "💰 Giá",
                 "value": f"{quote.get('price', 0):,.0f} đ",
                 "inline": True},
            ],
        }

    @staticmethod
    def _color_for(signal: str) -> int:
        return {
            "STRONG_BUY": 3066993,  # Green
            "BUY": 3066993,
            "NEUTRAL": 3447003,     # Blue
            "SELL": 15158332,       # Red
            "STRONG_SELL": 15158332,
        }.get(signal, 3447003)
```

- [ ] **Step 5: Run test, verify pass**

Run: `PYTHONPATH=. pytest tests/test_notifier.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/notifier/telegram_bot.py src/notifier/discord_bot.py tests/test_notifier.py
git commit -m "feat(notifier): render AnalysisReport with dict backward-compat"
```

---

## Task 13: Update main.py print format

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Overwrite main.py**

Overwrite `main.py`:

```python
import argparse
import sys
import io
import logging
from dotenv import load_dotenv

# Fix UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.core.analyzer import Analyzer
from src.notifier.telegram_bot import TelegramNotifier
from src.notifier.discord_bot import DiscordNotifier
from src.scoring.aggregator import AnalysisReport

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def print_report(report: AnalysisReport) -> None:
    info = report.info or {}
    quote = report.quote or {}
    symbol = report.symbol or ''

    price_vnd = quote.get('price', 0) * 1000
    change_pct = quote.get('change_pct', 0)

    print("\n" + "=" * 60)
    print(f"BÁO CÁO PHÂN TÍCH: {symbol}")
    print("=" * 60)
    print(f"🏢 Công ty: {info.get('company_name', '')} | Ngành: {info.get('industry', 'N/A')} | Sàn: {info.get('exchange', '')}")
    print(f"💰 Giá: {price_vnd:,.0f}đ ({change_pct:+.2f}%)")
    print(f"📦 KL: {quote.get('volume', 0):,.0f} cp")

    if report.circuit_breaker and report.circuit_breaker.get('warning'):
        print(f"⚠️  {report.circuit_breaker['warning']}")

    print()
    print(f"🎯 Composite Score: {report.composite:.0f}/100 → {report.final_signal.value}")
    print("-" * 60)
    print(f"{'Strategy':<22} {'Score':>5}  {'Signal':<12}  Reason")
    print("-" * 60)
    for c in report.cards:
        name = (c.strategy_name[:21]).ljust(22)
        signal = c.signal.value.ljust(12)
        reason = (c.reason[:30]).ljust(30)
        print(f"{name} {c.score:>5}  {signal}  {reason}")
    print("-" * 60)
    print("🤖 LLM Analysis:")
    print(report.narrative or "(no narrative)")
    print("=" * 60)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="VN Stock Daily Analysis")
    parser.add_argument("--symbol", type=str, default="VNM.HO")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--force-run", action="store_true")
    args = parser.parse_args()

    if not args.symbol:
        logger.error("Vui lòng cung cấp --symbol")
        sys.exit(1)

    analyzer = Analyzer()
    result = analyzer.analyze(args.symbol)

    if isinstance(result, dict):  # failed path returns dict
        print("\n" + "=" * 60)
        print(f"BÁO CÁO PHÂN TÍCH: {result.get('symbol', args.symbol)}")
        print("=" * 60)
        print(f"❌ LỖI: {result.get('error')}")
        sys.exit(1)

    print_report(result)
    print("✅ Trạng thái: Hoàn thành")

    if not args.dry_run:
        logger.info("Sending notifications...")
        TelegramNotifier().send_report(result)
        DiscordNotifier().send_report(result)
    else:
        logger.info("[Dry Run] Skipped sending notifications.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test**

Run: `PYTHONPATH=. python main.py --symbol VNM.HO --dry-run`
Expected: in ra bảng điểm đầy đủ, không crash. (Cần `GEMINI_API_KEY` hợp lệ để LLM trả lời; không có key vẫn phải in báo lỗi rõ ràng.)

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: update main.py to render scoring report output"
```

---

## Task 14: End-to-end verification

**Files:** none (chạy manual + full test suite)

- [ ] **Step 1: Full test suite**

Run: `PYTHONPATH=. pytest tests/ -v`
Expected: tất cả PASS. Ghi lại số test xanh. Nếu có test cũ fail vì format dict đổi, cập nhật riêng.

- [ ] **Step 2: Lint**

Run: `flake8 src/ main.py --max-line-length=120`
Expected: không lỗi mới được giới thiệu.

- [ ] **Step 3: Smoke thử với mã thật**

Với key LLM hợp lệ trong `.env`:

```bash
PYTHONPATH=. python main.py --symbol VNM.HO --dry-run
PYTHONPATH=. python main.py --symbol FPT.HO --dry-run
PYTHONPATH=. python main.py --symbol HPG --dry-run
```

Kiểm mắt:
- Composite trong [0, 100]
- Bảng điểm hiển thị 4-6 dòng
- Narrative tiếng Việt không trái ngược final_signal

- [ ] **Step 4: Telegram/Discord thủ công (optional)**

Nếu có config: chạy không `--dry-run` một lần, kiểm tra tin nhắn render đúng trên ít nhất 1 kênh.

- [ ] **Step 5: Update README development status**

Mở `README.md`, cập nhật bảng tính năng (nếu cần) — đánh dấu "Strategies YAML được kích hoạt (multi-angle scoring)" ở Phase 2 hoặc tạo Phase 2.5.

Trong `README.md` tìm block:

```
| Chiến lược YAML (MA, RSI, Volume...) | ✅ Phase 2 |
```

Đổi thành:

```
| Chiến lược YAML (MA, RSI, Volume...) | ✅ Phase 2 |
| Multi-Angle Scoring Engine (composite 0-100) | ✅ Phase 2.5 |
```

- [ ] **Step 6: Final commit**

```bash
git add README.md
git commit -m "docs: mark scoring engine as shipped in README"
```

---

## Definition of Done

- [ ] 6 YAML files validated by Pydantic schema, all loaded cleanly by `StrategyRunner.load_dir`.
- [ ] 3 CSV fixtures present, unit tests for indicators/strategy_runner/aggregator all pass.
- [ ] Integration test `tests/test_analyzer_scoring.py` — bullish composite ≥ 55, bearish composite ≤ 55.
- [ ] `PYTHONPATH=. python main.py --symbol VNM.HO --dry-run` prints a scoring table without crashing.
- [ ] Notifier supports both `AnalysisReport` and legacy dict.
- [ ] `flake8 src/ main.py --max-line-length=120` introduces no new errors.
- [ ] All commits are small, logical, and messages describe the "why".
