# Prompt 04 — DCF Intrinsic Value Model

## Mục tiêu
Bổ sung **module DCF (Discounted Cash Flow)** vào scoring engine, tính intrinsic value per share và so sánh với giá thị trường. Đây là chỉ số nền tảng cho các persona Buffett / Graham / Lynch (đã thêm ở Prompt 01) — không có DCF, các persona đó chỉ định tính chứ không định lượng được "margin of safety".

Lấy cảm hứng từ FinceptTerminal (DCF model là 1 trong 18 QuantLib modules) nhưng cài đặt thuần Python.

## Bối cảnh codebase
- Financial data lấy qua `src/data_provider/vnstock_provider.py::get_financial_report(symbol)` — hiện chỉ trả Income Statement quý. **Cần mở rộng** để lấy thêm: Cash Flow Statement, Balance Sheet, để có FCF.
- `src/scoring/fundamental.py` — đang có `calculate_f_score`. DCF nên ở file riêng, không nhét vào đây.
- `AnalysisReport` ở `src/scoring/aggregator.py` — cần thêm field `valuation`.
- Analyzer tại `src/core/analyzer.py` — gọi scoring pipeline; chèn DCF sau bước indicator.
- Thị trường VN: Giá OHLCV từ KBS trả **nghìn đồng** (1 đơn vị = 1000đ). `main.py` nhân `*1000` để hiển thị. DCF output phải thống nhất đơn vị — đề xuất **VND nguyên gốc** (không nghìn), và convert khi hiển thị.

## Yêu cầu

### 1. Mở rộng Data Provider

Sửa `src/data_provider/base.py` — thêm abstract method:
```python
@abstractmethod
def get_financials_bundle(self, symbol: str, years: int = 5) -> Dict[str, Any]:
    """
    Trả dict chứa:
    {
        "income_statement": DataFrame (năm),
        "cash_flow": DataFrame (năm),
        "balance_sheet": DataFrame (năm),
        "ratios": DataFrame (năm),    # ROE, ROA, debt/equity, ...
        "shares_outstanding": float,
        "currency": "VND"
    }
    Ít nhất `years` năm gần nhất, sắp xếp cũ → mới.
    """
    pass
```

Implement trong `src/data_provider/vnstock_provider.py`:
- vnstock v3 có `client.finance.income_statement(period='year')`, `cash_flow(period='year')`, `balance_sheet(period='year')`, `ratio(period='year')`.
- Xử lý trường hợp thiếu dữ liệu — trả DataFrame rỗng chứ không raise.
- Log warning nếu source không có đủ `years` năm.

### 2. Tạo `src/scoring/valuation.py`

```python
"""DCF intrinsic value + valuation grade."""
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd


@dataclass
class DCFAssumptions:
    growth_high: float = 0.15        # Giai đoạn tăng trưởng mạnh (năm 1-5), 15%/năm
    growth_terminal: float = 0.03    # Tăng trưởng vĩnh viễn, 3%/năm
    discount_rate: float = 0.12      # WACC giả định cho VN (cao hơn US do rủi ro quốc gia)
    years_high_growth: int = 5
    years_fade: int = 5              # 5 năm fade từ growth_high → growth_terminal


@dataclass
class ValuationResult:
    intrinsic_value_per_share: Optional[float]  # VND
    market_price: float                          # VND
    upside_pct: Optional[float]                  # (intrinsic - market) / market * 100
    margin_of_safety_pct: Optional[float]        # Tương tự upside_pct nhưng ≥ 0 mới có ý nghĩa
    fcf_base: Optional[float]                    # FCF bình quân 3 năm, làm base
    fcf_trend: str                               # "GROWING" | "STABLE" | "DECLINING" | "NEGATIVE"
    assumptions: DCFAssumptions
    grade: str                                   # "UNDERVALUED" | "FAIR" | "OVERVALUED" | "SPECULATIVE"
    notes: List[str]                             # Cảnh báo: FCF âm, data thiếu, etc.


class DCFEngine:
    """
    Simple two-stage DCF (high growth → fade → terminal).
    VN-specific defaults: discount_rate 12% (cao hơn US ~8-10% vì country risk premium).
    """

    def __init__(self, assumptions: Optional[DCFAssumptions] = None):
        self.a = assumptions or DCFAssumptions()

    def compute(
        self,
        financials_bundle: dict,
        market_price_vnd: float,
    ) -> ValuationResult:
        ...
```

**Logic triển khai:**

1. **Tính FCF lịch sử** từ cash_flow DataFrame:
   - `FCF = Operating Cash Flow - CapEx` (tìm cột có key chứa "operating" và "capex"/"investing", tolerant với tên cột tiếng Việt của vnstock).
   - Lấy 3 năm gần nhất, bình quân → `fcf_base`.
   - Nếu mọi năm âm → `grade = "SPECULATIVE"`, `intrinsic_value = None`, thêm note "FCF âm, không định giá được bằng DCF". Return sớm.

2. **Phân loại `fcf_trend`**:
   - So sánh FCF 3 năm: nếu tăng đều → GROWING; nếu giảm đều → DECLINING; biến thiên < 20% → STABLE; có năm âm → flag trong notes.

3. **Project FCF** 10 năm:
   - Năm 1-5: `fcf *= (1 + growth_high)`
   - Năm 6-10: growth linear fade từ `growth_high` xuống `growth_terminal`.
   - Terminal value (cuối năm 10): `TV = FCF_year10 * (1 + growth_terminal) / (discount_rate - growth_terminal)`.

4. **Discount về hiện tại**:
   - `PV = Σ FCF_t / (1 + r)^t + TV / (1 + r)^10`

5. **Chia cho shares_outstanding**:
   - `intrinsic_value_per_share = PV / shares_outstanding`.
   - Nếu `shares_outstanding <= 0` hoặc None → grade "SPECULATIVE", return note.

6. **Grade**:
   - `upside_pct >= 30%` → UNDERVALUED
   - `-10% <= upside_pct < 30%` → FAIR
   - `upside_pct < -10%` → OVERVALUED

7. **Adjust assumptions cho VN**:
   - Nếu market cap < 1000 tỷ VND (small cap VN) → `discount_rate = 0.14` (thêm 2% premium).
   - Nếu ngành = "Ngân hàng" / "Bảo hiểm" → DCF **không phù hợp**, return grade "SPECULATIVE" với note "DCF không phù hợp cho ngành tài chính — dùng P/B hoặc Dividend Discount Model". (Có thể check industry qua `info.industry` truyền vào từ analyzer.)

### 3. Extend `AnalysisReport`

Sửa `src/scoring/aggregator.py`:
```python
valuation: Optional["ValuationResult"] = None
```
Forward reference, không import trực tiếp.

### 4. Tích hợp vào Analyzer

Sửa `src/core/analyzer.py`:
- Khởi tạo `self.dcf_engine = DCFEngine()` trong `__init__`.
- Sau bước 6 (Score Aggregation), thêm:
  ```python
  try:
      bundle = self.router.execute_with_fallback("get_financials_bundle", normalized_symbol, 5)
      market_price_vnd = quote.get('price', 0) * 1000  # KBS returns nghìn đồng
      valuation = self.dcf_engine.compute(bundle, market_price_vnd, industry=info.get('industry'))
      report.valuation = valuation
  except Exception as e:
      logger.warning(f"DCF failed for {normalized_symbol}: {e}")
      report.valuation = None
  ```
- **Quan trọng**: DCF fail KHÔNG được làm crash analyzer. Bắt exception, log, tiếp tục.

### 5. Hiển thị

**Telegram** (`src/notifier/telegram_bot.py`), thêm sau risk section:
```
💎 *Định giá DCF* (`{grade}`):
  • Intrinsic: `{iv:,.0f}đ/cp`
  • Market: `{mp:,.0f}đ/cp`
  • Upside: `{upside:+.1f}%` | MoS: `{mos:+.1f}%`
  • FCF base: `{fcf:,.0f}đ` ({trend})
{notes nếu có: "⚠️ " + note}
```
Skip toàn section nếu `valuation is None` hoặc `intrinsic_value_per_share is None` (ngành tài chính / FCF âm) — nhưng **vẫn in note** nếu grade == SPECULATIVE.

**Discord** (`src/notifier/discord_bot.py`): thêm 1 field "💎 Định giá DCF" tương tự, đặt sau field Rủi ro.

**main.py** in ra terminal: thêm 3-4 dòng print sau SCORECARD BREAKDOWN.

### 6. Tiêm context cho Persona Agents

Nếu Prompt 01 (investor personas) đã merge: sửa `src/agents/skill_agent.py` để khi user chọn skill BUFFETT/GRAHAM/LYNCH, bơm thêm `valuation` vào context prompt gửi LLM. Format:
```
DCF Intrinsic Value: {iv:,.0f}đ/cp
Market Price: {mp:,.0f}đ/cp
Margin of Safety: {mos:.1f}%
Valuation Grade: {grade}
```

## Test
Tạo `tests/test_valuation.py`:
1. Bundle giả lập FCF tăng đều → assert `grade == UNDERVALUED` khi market price thấp hơn intrinsic 30%.
2. Bundle FCF toàn số âm → assert `grade == SPECULATIVE` và `intrinsic_value_per_share is None`.
3. Ngành "Ngân hàng" → assert notes chứa "không phù hợp cho ngành tài chính".
4. `shares_outstanding == 0` → graceful return, không ZeroDivisionError.
5. Assumption sensitivity: tăng `discount_rate` 2% phải giảm intrinsic value (sanity check).

## Không làm
- Không implement DDM, APV, residual income — chỉ DCF đơn giản.
- Không backtest DCF historical — scope khác.
- Không fetch data nếu bundle đã có trong analyzer context.

## Commit
```
feat(scoring): add two-stage DCF intrinsic value with VN-specific assumptions
```
