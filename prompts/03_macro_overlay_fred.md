# Prompt 03 — Macro Overlay từ FRED (Fed Rate / DXY / US10Y) trong báo cáo

## Mục tiêu
Bổ sung **MacroProvider** lấy dữ liệu vĩ mô Mỹ từ FRED (Federal Reserve Economic Data — free, public, không cần key) và đính kèm vào báo cáo Telegram/Discord. Thị trường VN rất nhạy với Fed rate, DXY (US Dollar Index), US 10Y yield — các chỉ số này ảnh hưởng dòng vốn ngoại đổ vào/ra HOSE.

Lấy cảm hứng từ FinceptTerminal (100+ data connectors gồm FRED, IMF, World Bank) nhưng cài đặt tối giản, chỉ 1 file Python.

## Bối cảnh codebase
- Data provider pattern: `src/data_provider/base.py` định nghĩa `BaseDataProvider` (dành cho cổ phiếu VN). **Không ép MacroProvider kế thừa class này** — nó là một interface khác.
- `src/data_provider/vnstock_provider.py` làm ví dụ style code.
- `fallback_router.py` để router giữa các provider — không liên quan ở đây.
- Report flow: `analyzer.py` → build `AnalysisReport` → `main.py` đẩy vào `report_data` dict → `telegram_bot.send_report()` / `discord_bot.send_report()`.
- Env config qua `.env` (python-dotenv).

## FRED API (không cần API key cho endpoint CSV)
- Public CSV endpoint: `https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}`
- Tuy nhiên FRED khuyến khích dùng API key (free) qua `https://api.stlouisfed.org/fred/series/observations`.
- Series IDs cần dùng:
  - `DFF` — Effective Federal Funds Rate (daily)
  - `DTWEXBGS` — US Dollar Index (broad, daily)
  - `DGS10` — US 10-Year Treasury Yield (daily)
  - `DGS2` — US 2-Year Treasury Yield (daily, để tính yield curve 10Y-2Y)
  - `VIXCLS` — VIX (risk appetite proxy)

## Yêu cầu

### 1. Tạo `src/data_provider/macro_provider.py`

```python
"""Macro overlay: Fed Funds Rate, DXY, US Treasury yields, VIX từ FRED (public CSV)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import requests
import pandas as pd
from io import StringIO

logger = logging.getLogger(__name__)


@dataclass
class MacroSnapshot:
    as_of: str                          # ISO date
    fed_funds_rate: Optional[float]     # %
    fed_funds_rate_delta_30d: Optional[float]  # điểm % thay đổi 30 ngày
    dxy: Optional[float]                # US Dollar Index
    dxy_delta_30d_pct: Optional[float]  # % thay đổi 30 ngày
    us10y: Optional[float]              # %
    us2y: Optional[float]               # %
    yield_curve_10y_2y: Optional[float] # US10Y - US2Y (điểm %)
    vix: Optional[float]
    regime: str                         # "RISK_ON" | "RISK_OFF" | "NEUTRAL"
    notes: list                         # Danh sách cảnh báo macro cho thị trường VN


class FREDMacroProvider:
    """
    Lấy dữ liệu FRED qua public CSV endpoint (không cần key).
    Có cache đơn giản in-memory + tuỳ chọn cache file để tránh spam FRED.
    """
    BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    SERIES = {
        "fed_funds_rate": "DFF",
        "dxy": "DTWEXBGS",
        "us10y": "DGS10",
        "us2y": "DGS2",
        "vix": "VIXCLS",
    }

    def __init__(self, cache_ttl_hours: int = 6, timeout: int = 10):
        self._cache: Dict[str, tuple] = {}  # series_id -> (ts, df)
        self.ttl = timedelta(hours=cache_ttl_hours)
        self.timeout = timeout

    def _fetch_series(self, series_id: str) -> pd.DataFrame:
        """Fetch + cache một series. Trả DataFrame với cột date, value."""
        ...

    def get_snapshot(self) -> MacroSnapshot:
        """Gộp tất cả series → MacroSnapshot, xác định regime."""
        ...
```

**Logic regime classification (đơn giản, dựa trên rule):**
- `RISK_OFF` nếu: `vix > 25` HOẶC `yield_curve < 0` (inverted) HOẶC `dxy_delta_30d_pct > 2`
- `RISK_ON` nếu: `vix < 15` VÀ `yield_curve > 0.5` VÀ `dxy_delta_30d_pct < -1`
- Còn lại `NEUTRAL`

**Notes tự sinh cho thị trường VN (append vào list `notes`):**
- Nếu `dxy_delta_30d_pct > 1.5` → `"DXY tăng → áp lực rút vốn ngoại khỏi HOSE"`
- Nếu `fed_funds_rate_delta_30d > 0.25` → `"Fed thắt chặt → SBV có thể phải nâng lãi suất theo"`
- Nếu `yield_curve < 0` → `"Yield curve đảo ngược → tín hiệu suy thoái Mỹ, VN thường chịu ảnh hưởng trễ 6–9 tháng"`
- Nếu `vix > 30` → `"VIX cao → risk-off toàn cầu, tránh midcap/penny VN"`

**Xử lý lỗi:**
- Nếu FRED request fail → log warning, trả `MacroSnapshot` với tất cả field `None` trừ `as_of` và `regime="NEUTRAL"`, `notes=["Macro data unavailable"]`.
- Timeout 10s cho mỗi request, không block main flow quá lâu.

### 2. Tích hợp vào Analyzer

Sửa `src/core/analyzer.py` (đọc trước khi sửa):
- Thêm:
  ```python
  from src.data_provider.macro_provider import FREDMacroProvider
  ```
- Khởi tạo `self.macro_provider = FREDMacroProvider()` trong `__init__` (với try/except — không được để fail là crash analyzer).
- Sau khi có `report`, gọi `macro = self.macro_provider.get_snapshot()` và gán `report.macro = macro`.

Sửa `src/scoring/aggregator.py`:
- Thêm `macro: Optional["MacroSnapshot"] = None` vào `AnalysisReport` (forward reference).

### 3. Thêm env toggle (optional)

Trong `.env.example` (nếu có), thêm:
```
# Macro overlay
MACRO_OVERLAY_ENABLED=true
FRED_CACHE_TTL_HOURS=6
```

Trong analyzer, đọc `os.getenv("MACRO_OVERLAY_ENABLED", "true").lower() == "true"` để bật/tắt.

### 4. Hiển thị trong Telegram

Sửa `src/notifier/telegram_bot.py`. Thêm section trước dòng `"\n---"` cuối:

```
🌐 *Macro Overlay* (`{regime}`):
  • Fed Funds: `{ff:.2f}%` ({ff_delta:+.2f} 30D)
  • DXY: `{dxy:.2f}` ({dxy_delta:+.2f}% 30D)
  • US10Y: `{us10y:.2f}%` | Curve 10Y-2Y: `{curve:+.2f}`
  • VIX: `{vix:.1f}`
{notes nếu có: "⚠️ " + note newline}
```

### 5. Hiển thị trong Discord

Sửa `src/notifier/discord_bot.py` — thêm 1 field:
```python
{
  "name": f"🌐 Macro Overlay ({regime})",
  "value": "…",  # multi-line format như Telegram
  "inline": False
}
```
Đặt field này NGAY TRƯỚC field cảnh báo (`⚠️ Cảnh Báo`) nếu có.

Nếu `regime == "RISK_OFF"` → thêm warning emoji vào title embed và đổi color warning (15105570 — cam) trừ khi đã có warning đỏ.

### 6. Cache file tuỳ chọn (đề phòng GitHub Actions chạy nhiều symbols)

Trong `FREDMacroProvider._fetch_series`, ngoài in-memory cache, hỗ trợ file cache tại `.cache/fred_{series_id}.parquet` với mtime TTL. Tạo thư mục `.cache/` nếu chưa có. Thêm `.cache/` vào `.gitignore` nếu chưa có.

## Test
Tạo `tests/test_macro_provider.py`:
1. Mock `requests.get` trả CSV giả → assert `get_snapshot()` parse đúng.
2. Mock request raise `ConnectionError` → assert fallback snapshot (None fields, regime NEUTRAL, notes chứa "unavailable").
3. Test regime classification với các combination input cụ thể.
4. Test cache hit (gọi 2 lần liên tiếp → `requests.get` chỉ được gọi 1 lần).

Chạy: `pytest tests/test_macro_provider.py -v`

## Không làm
- **Không** thêm API key FRED vào repo hoặc env mặc định — dùng public CSV endpoint, đủ cho use case này.
- Không cache vô thời hạn — TTL mặc định 6 giờ.
- Không block main analyzer > 15s nếu FRED chậm.
- Không gọi FRED khi chạy unit test (phải mock).

## Commit
```
feat(data_provider): add FRED macro overlay (Fed rate, DXY, yields, VIX) to daily report
```
