# Multi-Angle Scoring Engine — Design Spec

**Ngày:** 2026-04-18
**Trạng thái:** Draft (chờ user review)
**Sub-project:** #1 / 6 của lộ trình "cải thiện VN Stock Daily Analysis"
**Tham chiếu:** [Simplize.vn](https://simplize.vn) (điểm doanh nghiệp) · [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) (multi-angle analysis)

---

## 1. Mục tiêu

Biến 6 file YAML strategies (`src/strategies/*.yaml`) hiện đang "chết" thành **6 góc nhìn độc lập**. Mỗi góc chấm điểm 0-100 cho một mã cổ phiếu dựa trên rule cố định. Tổng hợp thành **composite score** có thể so sánh giữa các mã và qua thời gian. LLM đóng vai người **giải thích** điểm — không sửa, không bịa.

**Vì sao đáng làm**
- 6 file YAML đã có sẵn nhưng chưa được dùng → đang lãng phí code.
- Output hiện tại của analyzer là văn bản tự do từ LLM → không so sánh được giữa các mã, không theo dõi được qua ngày.
- Là nền tảng cho các sub-project tiếp theo: Screener VN30 (cần điểm để xếp hạng), Multi-Agent (cần score per-angle để tổng hợp), Historical Memory (cần con số để vẽ biểu đồ thời gian).

**Không làm gì trong sub-project này**
- Multi-stock screener (sub-project #2)
- News & sentiment (#4)
- Fundamental / P-E, ROE (#6)
- Multi-agent (#3)
- Backtest & auto-tune weights (sub-project riêng sau này)

---

## 2. Outcome demo

Chạy `python main.py --symbol VNM.HO --dry-run` sau khi hoàn thành sẽ in ra:

```
==================================================
BÁO CÁO PHÂN TÍCH: VNM.HO
==================================================
🏢 Công ty: CTCP Sữa Việt Nam | Ngành: Hàng tiêu dùng | Sàn: HOSE
💰 Giá: 61,300đ (+200đ / +0.33%)

🎯 Composite Score: 72/100 → BUY
┌──────────────────────┬───────┬──────────┬─────────────────────────────────────┐
│ Strategy             │ Score │ Signal   │ Reason                              │
├──────────────────────┼───────┼──────────┼─────────────────────────────────────┤
│ MA Crossover         │  85   │ BUY      │ Golden cross ngày 2026-04-15        │
│ RSI Divergence       │  55   │ NEUTRAL  │ RSI=58, chưa có phân kỳ             │
│ Volume Breakout      │  78   │ BUY      │ KL hôm nay = 1.8× TB20              │
│ Support / Resistance │  70   │ BUY      │ Gần hỗ trợ mạnh 60,500đ             │
│ Bollinger Bands      │  68   │ BUY      │ Chạm band giữa, đang hồi            │
│ VN30 Momentum        │  75   │ BUY      │ VN30 +1.2%, VNM beta 1.1            │
└──────────────────────┴───────┴──────────┴─────────────────────────────────────┘

🤖 LLM Analysis:
VNM đang có setup kỹ thuật tích cực với 5/6 tín hiệu đồng thuận mua...
(3-5 câu narrative)

✅ Trạng thái: Hoàn thành
```

---

## 3. Kiến trúc

### 3.1 Pipeline cũ vs mới

**Cũ (`src/core/analyzer.py`):**

```
DataProvider → Tính MA5/MA20/vol ngay trong analyzer → Build prompt → LLM → return text
```

Vấn đề: indicators chỉ 2 cái (MA5, MA20); YAML không tham gia; LLM tự quyết định khuyến nghị → không so sánh được, không test được, dễ bịa.

**Mới:**

```
main.py
  └─ Analyzer.analyze(symbol)
       ├─ DataProvider                 (đã có)    → OHLCV 180 phiên + quote + info
       ├─ IndicatorEngine      [MỚI]              → Tính 1 lần toàn bộ chỉ báo cần thiết
       ├─ StrategyRunner       [MỚI]              → Load N YAML → eval rules → [ScoreCard]
       ├─ ScoreAggregator      [MỚI]              → Composite score + final signal
       ├─ LLMExplainer         (refactor)         → Nhận score sẵn → giải thích tiếng Việt
       └─ Notifier             (đã có, tinh chỉnh format)
```

Nguyên tắc: **separation of concern**. Data tách khỏi compute tách khỏi rule tách khỏi narrative. Mỗi lớp test độc lập.

### 3.2 Ranh giới module

- **IndicatorEngine** biết về pandas/pandas-ta, không biết gì về YAML.
- **StrategyRunner** biết về YAML schema và rule evaluation, không biết gì về LLM.
- **ScoreAggregator** chỉ thao tác trên list `ScoreCard`, không biết gì về indicators.
- **LLMExplainer** nhận một `AnalysisReport` thuần dữ liệu, không gọi data provider.
- **Analyzer** (orchestrator) dán các mảnh lại.

---

## 4. Chi tiết component

### 4.1 `src/scoring/indicators.py` — IndicatorEngine

Trách nhiệm: nhận DataFrame OHLCV, return dict các chỉ báo đã tính, kèm giá trị "prev" (phiên trước) để rule có thể phát hiện sự kiện "vừa xảy ra" (ví dụ golden cross).

**Interface:**

```python
class IndicatorEngine:
    def compute(self, df: pd.DataFrame) -> IndicatorSet:
        ...
```

**IndicatorSet** là dataclass chứa giá trị phiên hiện tại và phiên trước:

```
IndicatorSet(
    close: float, prev_close: float,
    MA5, MA10, MA20, MA50, MA200,
    prev_MA5, prev_MA20, prev_MA50,
    RSI14, prev_RSI14,
    MACD, MACD_signal, MACD_hist, prev_MACD_hist,
    BB_upper, BB_mid, BB_lower,
    ATR14,
    volume, volume_ma20, volume_ratio,
    support_20, resistance_20,     # min/max 20 phiên
    ...
)
```

Cài đặt: dùng `pandas-ta`. Xử lý edge case: DataFrame < 50 phiên → raise `InsufficientDataError`. Một chỉ báo bị NaN (thường do chưa đủ lookback) → giá trị `None` và StrategyRunner sẽ skip rule cần chỉ báo đó.

### 4.2 `src/scoring/strategy_runner.py` — StrategyRunner

Trách nhiệm: load YAML, validate schema, evaluate rules trên IndicatorSet, return `ScoreCard`.

**YAML schema mới:**

```yaml
name: "MA Crossover"           # required, human-readable
description: "..."              # optional
weight: 1.0                     # required, float > 0
enabled: true                   # required, bool
indicators_required:            # optional — skip strategy nếu thiếu
  - MA20
  - MA50
rules:                          # required, ít nhất 1 rule
  - when: "MA20 > MA50 and prev_MA20 <= prev_MA50"
    score: 85
    signal: BUY
    reason: "Golden cross: MA20 vừa cắt lên MA50"

  - when: "MA20 > MA50"
    score: 65
    signal: BUY_WEAK
    reason: "MA20 trên MA50 — xu hướng tăng"

  - when: "MA20 < MA50 and prev_MA20 >= prev_MA50"
    score: 15
    signal: SELL
    reason: "Death cross"

  - default: true               # đúng 1 rule có default: true, ở cuối
    score: 40
    signal: NEUTRAL
    reason: "MA20 dưới MA50"
```

**Rule evaluation:**
- Dùng [`asteval`](https://newville.github.io/asteval/) — restricted AST eval, không cho import / builtins nguy hiểm.
- Biến truyền vào: tất cả field của IndicatorSet.
- Duyệt rules theo thứ tự; rule đầu tiên `when=True` thắng; nếu không rule nào, dùng `default: true`.
- Nếu thiếu indicator cần thiết (giá trị `None`): skip rule đó, tiếp tục.

**Signal enum per-strategy** (granular): `STRONG_BUY | BUY | BUY_WEAK | NEUTRAL | SELL_WEAK | SELL | STRONG_SELL`

**Signal enum composite (final)** — rút gọn: `STRONG_BUY | BUY | HOLD | SELL | STRONG_SELL` (mapping ở mục 4.3).

**Validation (Pydantic):**
- `score ∈ [0, 100]`
- `weight > 0`
- Bắt buộc có **đúng 1** rule với `default: true` và phải là rule cuối cùng (tránh coverage holes, tránh ambiguity khi debug)
- `when` parse được bằng asteval không raise

**Output ScoreCard:**

```python
@dataclass
class ScoreCard:
    strategy_name: str
    score: int               # 0-100
    signal: Signal
    reason: str
    weight: float
    rule_matched: int        # index của rule match, phục vụ debug
```

### 4.3 `src/scoring/aggregator.py` — ScoreAggregator

```python
class ScoreAggregator:
    def aggregate(self, cards: list[ScoreCard]) -> AnalysisReport:
        composite = sum(c.score * c.weight for c in cards) / sum(c.weight for c in cards)
        final_signal = self._bucket(composite)
        return AnalysisReport(composite=composite, final_signal=final_signal, cards=cards)
```

**Bucket:**

| Composite | Final Signal |
|-----------|--------------|
| 80–100 | STRONG_BUY |
| 65–79  | BUY |
| 40–64  | HOLD |
| 20–39  | SELL |
| 0–19   | STRONG_SELL |

### 4.4 `src/core/analyzer.py` — Orchestrator (refactor)

```python
class Analyzer:
    def __init__(self, strategy_dir="src/strategies"):
        self.router = FallbackRouter([VNStockProvider()])
        self.validator = VNStockValidator()
        self.circuit_breaker = CircuitBreakerHandler()
        self.indicators = IndicatorEngine()
        self.strategy_runner = StrategyRunner.load_dir(strategy_dir)
        self.aggregator = ScoreAggregator()
        self.explainer = LLMExplainer()

    def analyze(self, symbol: str) -> AnalysisReport:
        # 1. Validate & fetch — như cũ
        # 2. indicator_set = self.indicators.compute(df)
        # 3. cards = self.strategy_runner.run(indicator_set)
        # 4. report = self.aggregator.aggregate(cards)
        # 5. report.narrative = self.explainer.explain(report, info, quote)
        # 6. return report
```

### 4.5 `LLMExplainer` — giải thích, không chấm điểm

Prompt template (tiếng Việt, cứng rắn):

```
Bạn là chuyên gia phân tích kỹ thuật chứng khoán Việt Nam. Hệ thống đã TÍNH SẴN điểm và tín hiệu.

NHIỆM VỤ DUY NHẤT: Giải thích kết quả bằng 3-5 câu tiếng Việt.

TUYỆT ĐỐI KHÔNG:
- Đổi điểm số
- Đưa khuyến nghị trái ngược signal
- Bịa thêm chỉ báo không có trong dữ liệu

Dữ liệu:
Mã: {symbol}
Composite: {composite} → {final_signal}
Chi tiết:
{strategy_cards_as_table}
Thông tin công ty: {info}
Giá hiện tại: {quote}
```

### 4.6 Notifier (tinh chỉnh)

`src/notifier/telegram_bot.py` và `discord_bot.py` nhận `AnalysisReport` thay vì dict cũ. Render bảng điểm bằng Markdown (Telegram) hoặc Embed field (Discord). Giữ backward-compat: nếu truyền dict cũ vẫn chạy được trong kỳ chuyển đổi.

---

## 5. Thay đổi file cụ thể

**Tạo mới**

| File | Mục đích |
|---|---|
| `src/scoring/__init__.py` | package marker |
| `src/scoring/indicators.py` | IndicatorEngine + IndicatorSet |
| `src/scoring/strategy_runner.py` | YAML loader + Pydantic model + asteval runner |
| `src/scoring/aggregator.py` | ScoreAggregator + ScoreCard + AnalysisReport |
| `src/scoring/signals.py` | Signal enum + bucket function |
| `tests/test_indicators.py` | Unit test IndicatorEngine với fixture CSV |
| `tests/test_strategy_runner.py` | Load & eval 6 YAML, test edge case |
| `tests/test_aggregator.py` | Composite math, bucket boundaries |
| `tests/test_analyzer_scoring.py` | Integration: symbol → report |
| `tests/fixtures/ohlcv_bullish.csv` | 200 phiên kịch bản xu hướng tăng |
| `tests/fixtures/ohlcv_bearish.csv` | 200 phiên kịch bản xu hướng giảm |
| `tests/fixtures/ohlcv_sideways.csv` | 200 phiên kịch bản đi ngang |

**Sửa**

| File | Thay đổi |
|---|---|
| `src/core/analyzer.py` | Refactor: dùng pipeline mới, trả `AnalysisReport` thay vì dict |
| `src/core/llm_client.py` | Có thể giữ nguyên; chỉ LLMExplainer đổi prompt |
| `src/strategies/ma_crossover.yaml` | Thêm `weight`, `enabled`, `indicators_required`, `rules` |
| `src/strategies/rsi_divergence.yaml` | Như trên |
| `src/strategies/volume_breakout.yaml` | Như trên |
| `src/strategies/support_resistance.yaml` | Như trên |
| `src/strategies/bollinger_bands.yaml` | Như trên |
| `src/strategies/vn30_momentum.yaml` | Như trên |
| `src/notifier/telegram_bot.py` | Render bảng điểm |
| `src/notifier/discord_bot.py` | Render bảng điểm (embed fields) |
| `main.py` | Print theo format demo ở mục 2 |
| `requirements.txt` | Thêm `asteval`, `pydantic>=2`, `pandas-ta` (nếu chưa có) |

---

## 6. Rủi ro & mitigation

| Rủi ro | Mitigation |
|---|---|
| Rule expression bị inject code độc | Dùng `asteval` (restricted AST, no `__import__`, no `exec`); ghi test anti-injection |
| Weights được chọn tùy tiện → score vô nghĩa | Khởi điểm tất cả `weight=1.0`; expose qua config; tinh chỉnh chỉ sau khi có backtest (sub-project sau) |
| YAML dễ viết sai → chạy runtime mới báo lỗi | Pydantic validate ngay khi `load_dir()`; Analyzer khởi tạo fail nhanh |
| LLM vẫn bịa / đổi signal | Prompt cứng rắn + post-check: nếu LLM text chứa từ trái ngược signal thì log warning |
| Indicator thiếu dữ liệu (mã mới lên sàn) | `InsufficientDataError` → Analyzer return report với note "thiếu dữ liệu", không crash |
| Ảnh hưởng output cũ (dict) làm vỡ Telegram/Discord | Notifier nhận cả `AnalysisReport` và dict (adapter trong kỳ chuyển đổi); xoá nhánh dict sau khi migrate xong |
| Test dùng data vnstock thật → flaky | Mọi test unit dùng fixture CSV; chỉ 1 test integration gọi mạng, marker `@pytest.mark.network`, bỏ qua mặc định |

---

## 7. Testing strategy

**Unit**
- `IndicatorEngine`: với fixture CSV đã biết trước, assert giá trị MA20/RSI/… đúng tới 2 chữ số thập phân.
- `StrategyRunner`: load từng YAML, feed IndicatorSet giả, assert đúng rule match và đúng score.
- `ScoreAggregator`: test composite math, test boundary bucket (79→BUY, 80→STRONG_BUY, …).
- `asteval` sandbox: viết test cố gắng eval `__import__('os').system(...)` → phải raise.

**Integration**
- `test_analyzer_scoring.py`: mock data provider trả fixture bullish → assert composite > 65 và final_signal ∈ {BUY, STRONG_BUY}. Tương tự bearish, sideways.

**Regression**
- Giữ các test hiện có trong `tests/test_analyzer.py` (có thể cần cập nhật assertion sang `AnalysisReport`).
- `pytest tests/ -v` phải xanh.

**Thủ công**
- `python main.py --symbol VNM.HO --dry-run`
- `python main.py --symbol FPT.HO --dry-run`
- `python main.py --symbol HPG --dry-run`
- Quan sát bảng điểm hợp lý với tình trạng thực của mã.

---

## 8. Tiêu chí hoàn thành (Definition of Done)

1. 6 YAML đã được mở rộng, tất cả pass Pydantic validation khi load.
2. 3 fixture CSV tồn tại; unit tests `pytest tests/test_indicators.py tests/test_strategy_runner.py tests/test_aggregator.py -v` xanh.
3. Test integration với fixture 3 kịch bản xanh.
4. `python main.py --symbol VNM.HO --dry-run` in bảng điểm đúng format mục 2 với dữ liệu thật.
5. Notifier Telegram & Discord render bảng điểm (kiểm thủ công ít nhất 1 lần mỗi kênh).
6. `flake8 src/ --max-line-length=120` không lỗi mới.
7. Commit đã chia theo từng logical step (không 1 commit khủng).

---

## 9. Câu hỏi mở (cần user xác nhận khi review)

1. **Weight khởi điểm**: tất cả = 1.0, hay bạn muốn set tay ngay đầu (ví dụ MA Crossover = 1.2, RSI = 0.8)?
2. **Bậc thang signal**: đang chọn 80/65/40/20. Bạn muốn đổi không (ví dụ chặt hơn: 85/70/45/25)?
3. **LLM model**: vẫn dùng `LLM_PRIMARY_MODEL` hiện tại (Gemini 2.0 flash) hay chuyển sang model reasoning mạnh hơn cho narrative?
4. **Backward compat**: mình đề xuất giữ dict adapter cho Notifier trong 1 kỳ chuyển đổi. Bạn muốn cắt đứt luôn (breaking) hay giữ adapter?

---

## 10. Sau khi sub-project này xong

Lộ trình các sub-project tiếp theo (ghi lại để không quên):

| # | Sub-project | Phụ thuộc |
|---|---|---|
| 2 | Multi-Stock Screener (quét VN30, xếp hạng top-10) | Cần #1 |
| 3 | Multi-Agent Architecture (technical/intel/risk/decision) | Có thể bắt đầu song song |
| 4 | News & Sentiment Pipeline (CafeF, VietStock) | Feed vào #3 |
| 5 | Historical Memory (SQLite lưu score theo ngày) | Cần #1 |
| 6 | Fundamental Analysis (P/E, P/B, ROE, so sánh ngành) | Độc lập |
