# Prompt 06 — Stock Screener cho toàn HOSE/HNX

## Mục tiêu
Xây dựng **screener** để lọc toàn bộ cổ phiếu trên HOSE/HNX theo tiêu chí (fundamental + technical + risk + valuation), xuất top N mã đáng phân tích sâu. Hiện tại user phải tự nhập mã (`--symbol VNM.HO`) — screener biến project từ "analyzer passive" thành "discovery engine".

Lấy cảm hứng từ stock screener của FinceptTerminal.

## Bối cảnh codebase
- `src/data_provider/vnstock_provider.py`: có `client.listing.symbols_by_exchange()` trả toàn bộ symbols theo sàn.
- Scoring pipeline đã có: IndicatorEngine → StrategyRunner → Aggregator → composite score.
- F-Score tại `src/scoring/fundamental.py`.
- Nếu Prompt 02 (risk) và Prompt 04 (DCF) đã merge, tái sử dụng trực tiếp.
- `Analyzer.analyze(symbol)` đã orchestrate toàn bộ → có thể tái dùng, nhưng **sẽ rất chậm** nếu gọi cho 1600+ mã HOSE. Screener cần nhanh, chỉ tính subset nhẹ.

## Yêu cầu

### 1. Tạo `src/screener/` package

```
src/screener/
├── __init__.py
├── universe.py        # Lấy + cache danh sách symbols
├── filters.py         # Các filter primitive
├── engine.py          # Orchestrator: fetch → filter → rank
└── presets.py         # Preset tiêu chí (Buffett-style, Lynch-style, v.v.)
```

### 2. `src/screener/universe.py`

```python
"""Lấy universe mã chứng khoán VN + metadata (ngành, market cap, liquidity)."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UniverseItem:
    symbol: str
    exchange: str           # HOSE | HNX | UPCOM
    company_name: str
    industry: str
    market_cap_bn: Optional[float]   # Tỷ VND
    avg_volume_20d: Optional[float]  # Khớp lệnh bình quân


class UniverseLoader:
    """
    Load + cache file .cache/universe_{date}.parquet để tránh spam vnstock.
    TTL 24h. Nếu cache miss hoặc hết hạn → fetch mới.
    """

    def load(self, exchanges: tuple = ("HOSE", "HNX")) -> List[UniverseItem]:
        ...

    def _fetch_from_vnstock(self, exchange: str) -> List[UniverseItem]:
        ...
```

**Lưu ý performance:**
- Fetch market_cap và avg_volume cho từng symbol là **1600 HTTP calls** → không khả thi.
- Dùng `listing.industries_icb()` hoặc `listing.symbols_by_industries()` nếu vnstock hỗ trợ.
- Nếu không có cách batch → chỉ fetch symbol list + industry, bỏ market_cap_bn ở universe, tính sau trong screener.

### 3. `src/screener/filters.py`

Filter primitives — mỗi filter là 1 callable nhận `row dict` (indicators + fundamentals + quote) → bool:

```python
def min_market_cap(bn_vnd: float):
    return lambda r: (r.get("market_cap_bn") or 0) >= bn_vnd

def min_liquidity(shares_per_day: float):
    return lambda r: (r.get("avg_volume_20d") or 0) >= shares_per_day

def fscore_at_least(threshold: int):
    return lambda r: (r.get("f_score") or 0) >= threshold

def composite_score_at_least(threshold: float):
    return lambda r: (r.get("composite_score") or 0) >= threshold

def rsi_in_range(lo: float, hi: float):
    return lambda r: lo <= (r.get("RSI14") or 0) <= hi

def price_above_ma(ma_key: str):
    return lambda r: (r.get("close") or 0) > (r.get(ma_key) or float("inf"))

def undervalued_dcf(min_upside_pct: float = 20):
    return lambda r: (r.get("dcf_upside_pct") or -999) >= min_upside_pct

def risk_grade_in(grades: tuple):
    return lambda r: r.get("risk_grade") in grades

def industry_in(industries: tuple):
    return lambda r: r.get("industry") in industries

def exclude_industry(industries: tuple):
    return lambda r: r.get("industry") not in industries
```

### 4. `src/screener/engine.py`

```python
from dataclasses import dataclass
from typing import List, Callable, Optional
import pandas as pd


@dataclass
class ScreenerConfig:
    universe_exchanges: tuple = ("HOSE", "HNX")
    filters: List[Callable] = None
    rank_by: str = "composite_score"  # Field để sort desc
    top_n: int = 20
    parallel_workers: int = 8          # ThreadPool cho fetch song song
    min_history_days: int = 200
    enable_dcf: bool = False           # Tắt mặc định — chậm
    enable_risk: bool = True


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
        indicator_engine,
        strategy_runner,
        aggregator,
        risk_engine=None,       # Optional, từ Prompt 02
        dcf_engine=None,        # Optional, từ Prompt 04
        universe_loader=None,
    ):
        ...

    def run(self, config: ScreenerConfig) -> ScreenerResult:
        ...
```

**Flow:**
1. `universe = UniverseLoader().load(config.universe_exchanges)` — 1600+ items.
2. **Parallel fetch** indicators + quote cho mọi symbol qua `ThreadPoolExecutor(max_workers=8)`. Mỗi worker:
   - Fetch historical 250 days (đủ MA200).
   - Fetch quote.
   - `IndicatorEngine.compute` → IndicatorSet.
   - `StrategyRunner.run` → ScoreCards → aggregate → composite_score.
   - Optional: F-Score (cần financial_report quý).
   - Optional: risk_grade (RiskEngine).
   - Optional: dcf_upside_pct (DCFEngine — chậm, tắt mặc định).
3. Build big DataFrame rows (1 row/symbol).
4. Apply filters sequentially (pandas boolean mask hoặc `apply`).
5. Sort theo `rank_by` desc, take top_n.
6. Return ScreenerResult.

**Error handling per symbol:**
- Try/except bao quanh mỗi symbol. Fail 1 mã không làm hỏng cả run.
- Track `coverage = success_count / total`.
- Log symbols fail ra `.cache/screener_errors_{date}.log`.

**Rate limiting:**
- vnstock có rate limit. Dùng `ThreadPoolExecutor` tối đa 8 workers. Có `time.sleep(0.05)` giữa batch nếu cần.
- Dùng `tqdm` progress bar.

### 5. `src/screener/presets.py`

Preset filter combinations:

```python
from src.screener.filters import *

def buffett_style():
    """Giá trị dài hạn: FCF dương, F-Score cao, DCF undervalued, large cap."""
    return [
        min_market_cap(5000),
        min_liquidity(100_000),
        fscore_at_least(7),
        undervalued_dcf(min_upside_pct=25),
        exclude_industry(("Ngân hàng", "Bảo hiểm", "Bất động sản")),
    ]

def lynch_growth():
    """Midcap tăng trưởng, composite cao."""
    return [
        min_market_cap(1000),
        min_liquidity(50_000),
        composite_score_at_least(70),
        rsi_in_range(40, 75),
    ]

def graham_defensive():
    """Margin of safety cực lớn, risk thấp."""
    return [
        min_market_cap(3000),
        fscore_at_least(8),
        undervalued_dcf(min_upside_pct=40),
        risk_grade_in(("LOW", "MEDIUM")),
    ]

def technical_breakout():
    """Tín hiệu kỹ thuật mạnh, không quan tâm fundamental."""
    return [
        min_liquidity(100_000),
        composite_score_at_least(75),
        rsi_in_range(55, 75),
        price_above_ma("MA50"),
        price_above_ma("MA200"),
    ]
```

### 6. CLI

Tạo `screener.py` ở root:
```bash
# Preset có sẵn
python screener.py --preset buffett_style --top 20

# Tuỳ biến
python screener.py --exchange HOSE,HNX \
  --min-cap 2000 --min-liquidity 50000 \
  --min-score 65 --rsi-min 40 --rsi-max 70 \
  --top 30 --output csv

# Nhanh: tắt DCF
python screener.py --preset lynch_growth --no-dcf
```

Output:
- Terminal: bảng top N với columns: rank, symbol, name, industry, price, score, signal, f_score, risk_grade, upside.
- Optional `--output csv` → ghi `screener_output/{date}_{preset}.csv`.
- Optional `--notify telegram` → gửi top 10 qua Telegram (reuse TelegramNotifier, format ngắn).

### 7. Cron integration (tuỳ chọn)

Thêm script `scripts/daily_screener.sh`:
```bash
#!/bin/bash
python screener.py --preset buffett_style --top 10 --notify telegram
python screener.py --preset technical_breakout --top 10 --notify telegram
```

Thêm workflow GitHub Actions `.github/workflows/weekly_screener.yml` chạy 1 lần/tuần (thứ 2, 7h sáng VN).

## Test
Tạo `tests/test_screener.py`:
1. **Filter primitive unit tests**: mỗi filter test 3 case (pass/fail/missing-key).
2. **Engine với mock data_provider** (10 symbols giả) → assert `coverage == 1.0`, top_n đúng kích thước.
3. **Preset smoke test**: load mỗi preset → assert callable list non-empty.
4. **Error resilience**: mock 1 trong 10 symbols raise → assert `coverage == 0.9`, other 9 vẫn có trong `rows`.
5. **Parallel correctness**: chạy với `parallel_workers=1` vs `=4` → assert kết quả identical (trừ thứ tự).

## Không làm
- Không fetch news / sentiment cho universe 1600 mã — quá chậm.
- Không chạy DCF mặc định (dùng `--enable-dcf` flag).
- Không scan realtime intraday — daily only.
- Không lọc UPCOM mặc định (thanh khoản quá thấp, nhiều mã rác).

## Hiệu năng mục tiêu
- 1600 symbols × fetch 250 days: ~3-5 phút với 8 workers. Nếu > 10 phút → optimize batch hoặc cache history file.
- Memory: ~200MB cho DataFrame kết quả. OK.

## Commit
```
feat(screener): add multi-criteria screener with presets for HOSE/HNX
```
