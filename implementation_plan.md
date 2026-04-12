# VN Stock Daily Analysis — Bản Kế Hoạch Chi Tiết

> **Mục tiêu:** Xây dựng hệ thống AI Agent phân tích chứng khoán Việt Nam hàng ngày, lấy cảm hứng trực tiếp từ `ZhuLinsen/daily_stock_analysis` (29.4k ⭐), bản địa hoá hoàn toàn cho HOSE / HNX / UPCOM.

---

## User Review Required

> [!IMPORTANT]
> Dự án này có scope lớn (~15+ modules). Mình đề xuất chia thành **4 Phase** để triển khai từng bước, mỗi phase có thể chạy độc lập và demo được. Bạn cần xác nhận thứ tự ưu tiên trước khi bắt đầu.

> [!WARNING]
> Thư viện `vnstock` hiện yêu cầu đăng ký API key (miễn phí) để tránh rate limit. Bạn cần tạo tài khoản tại [vnstocks.com](https://vnstocks.com) trước khi chạy phase 1.

---

## Kiến Trúc Tổng Quan

```
vn_stock_daily_analysis/
├── .github/workflows/          # GitHub Actions (zero-cost scheduling)
│   └── daily_analysis.yml
├── apps/
│   └── web/                    # TypeScript frontend (Vite + React)
├── src/
│   ├── core/                   # Core analysis engine
│   │   ├── analyzer.py         # Main analysis orchestrator
│   │   ├── llm_client.py       # LiteLLM router wrapper
│   │   └── report_generator.py # Report formatting
│   ├── data_provider/          # VN market data sources
│   │   ├── base.py             # Abstract data provider
│   │   ├── vnstock_provider.py # vnstock (TCBS/VCI/KBS)
│   │   ├── ssi_provider.py     # SSI FastConnect API
│   │   ├── vndirect_provider.py # VNDirect API
│   │   └── fallback_router.py  # Fallback chain logic
│   ├── news/                   # News & sentiment
│   │   ├── tavily_search.py    # Tavily web search
│   │   ├── brave_search.py     # Brave Search API
│   │   └── vn_news_scraper.py  # CafeF/VnExpress/VietStock
│   ├── agents/                 # Multi-Agent system
│   │   ├── technical_agent.py  # Technical analysis
│   │   ├── intel_agent.py      # News & intelligence
│   │   ├── risk_agent.py       # Risk assessment
│   │   ├── specialist_agent.py # Strategy specialist
│   │   └── decision_agent.py   # Final decision maker
│   ├── strategies/             # Trading strategies (YAML)
│   │   ├── ma_crossover.yaml   # Đường MA cắt nhau
│   │   ├── rsi_divergence.yaml # RSI phân kỳ
│   │   ├── volume_breakout.yaml# Breakout khối lượng
│   │   ├── support_resistance.yaml # Hỗ trợ/Kháng cự
│   │   ├── bollinger_bands.yaml # Bollinger Bands
│   │   └── vn30_momentum.yaml  # VN30 momentum strategy
│   ├── notifier/               # Push notification channels
│   │   ├── base.py
│   │   ├── telegram_bot.py
│   │   └── discord_bot.py
│   ├── market/                 # VN market specific
│   │   ├── trading_calendar.py # HOSE/HNX trading days & holidays
│   │   ├── stock_index.py      # VNIndex, HNX-Index, UPCOM-Index
│   │   └── sector_mapping.py   # VN sector/industry classification
│   └── utils/                  # Shared utilities
│       ├── config.py           # Environment config manager
│       ├── logger.py
│       └── cache.py
├── bot/                        # Telegram/Discord bot handlers
├── templates/                  # Report templates (Jinja2)
├── tests/
├── docker/
├── scripts/
├── main.py                     # Entry point
├── server.py                   # FastAPI server
├── requirements.txt
├── .env.example
└── pyproject.toml
```

---

## Phase 1: Foundation — Data Provider + Core Analysis (Tuần 1-2)

> Mục tiêu: Chạy được `python main.py` → lấy dữ liệu VN stock → gửi prompt tới LLM → nhận báo cáo phân tích → in ra terminal.

### 1.1 Data Provider Layer

#### [NEW] `src/data_provider/base.py`
- Abstract class `BaseDataProvider` với interface chuẩn:
  - `get_stock_info(symbol)` → thông tin cơ bản (tên, sàn, ngành)
  - `get_historical_data(symbol, start, end)` → OHLCV DataFrame
  - `get_realtime_quote(symbol)` → giá hiện tại, thay đổi, khối lượng
  - `get_financial_report(symbol)` → báo cáo tài chính
  - `get_company_profile(symbol)` → hồ sơ công ty

#### [NEW] `src/data_provider/vnstock_provider.py`
- Provider chính, sử dụng thư viện `vnstock`:
  ```python
  from vnstock.trading import Quote
  stock = Quote(symbol='VNM', source='VCI')
  df = stock.history(start='2024-01-01', end='2024-12-31')
  ```
- Source priority: `VCI` (local) → `KBS` (cloud-friendly) → `TCBS`
- Hỗ trợ: HOSE, HNX, UPCOM
- Data bao gồm: lịch sử giá, chỉ số tài chính, hồ sơ doanh nghiệp

#### [NEW] `src/data_provider/ssi_provider.py`
- Provider phụ (optional), dùng SSI FastConnect API
- Yêu cầu: `SSI_CONSUMER_ID`, `SSI_CONSUMER_SECRET`
- Ưu điểm: Realtime data, order book depth

#### [NEW] `src/data_provider/fallback_router.py`
- Kiến trúc fallback giống repo gốc:
  ```
  vnstock(VCI) → vnstock(KBS) → SSI API → VNDirect API
  ```
- Tự động chuyển source khi một source fail
- Logging chi tiết: source nào đã dùng, latency, errors

### 1.2 LLM Integration (LiteLLM Router)

#### [NEW] `src/core/llm_client.py`
- Wrapper quanh `litellm` library
- Auto-detect provider từ API key:
  ```python
  # Chỉ cần set key, hệ thống tự nhận diện
  GEMINI_API_KEY=xxx     → provider: gemini
  OPENAI_API_KEY=xxx     → provider: openai
  ANTHROPIC_API_KEY=xxx  → provider: anthropic
  OLLAMA_API_BASE=xxx    → provider: ollama
  ```
- Hỗ trợ fallback chain: nếu model A fail → tự chuyển sang model B
- LLM Channel config giống repo gốc:
  ```
  LLM_CHANNELS=primary,backup
  LLM_PRIMARY_PROTOCOL=openai
  LLM_PRIMARY_API_KEY=sk-xxx
  LLM_PRIMARY_MODELS=gpt-4o
  ```

### 1.3 Core Analyzer

#### [NEW] `src/core/analyzer.py`
- Orchestrator chính, flow:
  1. Lấy dữ liệu giá từ `data_provider`
  2. Tính technical indicators (MA, RSI, MACD, Bollinger...)
  3. Build prompt context (giá, indicators, tin tức)
  4. Gọi LLM qua `llm_client` để phân tích
  5. Parse LLM response → structured report
- Output: Decision Dashboard (Mua/Bán/Giữ + điểm số 0-100)

### 1.4 VN Market Specifics

#### [NEW] `src/market/trading_calendar.py`
- Lịch nghỉ lễ Việt Nam (Tết, 30/4, 2/9, Giỗ Tổ Hùng Vương...)
- Giờ giao dịch HOSE: Sáng 9:15-11:30, Chiều 13:00-14:30
- Kiểm tra ngày giao dịch trước khi chạy phân tích

#### [NEW] `src/market/stock_index.py`
- Chỉ số chính: VN-Index, HNX-Index, UPCOM-Index, VN30
- Đại bàn review: bao gồm cả thống kê gainers/losers/limit up/limit down

#### [NEW] `src/market/sector_mapping.py`
- Phân ngành theo chuẩn ICB Việt Nam
- Mapping: Ngân hàng, Bất động sản, Thép, Chứng khoán, Dầu khí, Bán lẻ, CNTT...

---

## Phase 2: Notification + Strategies + Scheduling (Tuần 3-4)

> Mục tiêu: Tự động phân tích hàng ngày + push báo cáo qua Telegram/Discord.

### 2.1 Notification Channels

#### [NEW] `src/notifier/telegram_bot.py`
- Push decision dashboard qua Telegram
- Hỗ trợ: text, markdown, image (chart screenshot)
- Config: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

#### [NEW] `src/notifier/discord_bot.py`
- Push qua Discord webhook + Discord bot
- Rich embeds với colors theo trading signal (🟢 Mua, 🟡 Giữ, 🔴 Bán)
- Config: `DISCORD_WEBHOOK_URL`, `DISCORD_BOT_TOKEN`

### 2.2 Trading Strategies (YAML)

#### [NEW] `src/strategies/*.yaml`
6 chiến lược mặc định cho VN market:
1. **MA Crossover** — Đường MA(20) cắt MA(50)
2. **RSI Divergence** — Phân kỳ RSI với giá
3. **Volume Breakout** — Đột phá khối lượng bất thường
4. **Support/Resistance** — Vùng hỗ trợ/kháng cự
5. **Bollinger Bands** — Tín hiệu từ dải Bollinger
6. **VN30 Momentum** — Chiến lược riêng cho rổ VN30

Mỗi file YAML chứa: tên, mô tả, prompt template, indicators cần dùng, parameters.

### 2.3 Scheduling

#### [NEW] `.github/workflows/daily_analysis.yml`
- Cron: `0 8 * * 1-5` (15:00 giờ VN, sau khi sàn đóng cửa)
- Check trading day trước khi chạy
- Manual trigger qua GitHub Actions UI
- Secrets: các API keys

#### [NEW] `main.py`
- Entry point với các mode:
  ```bash
  python main.py                    # Chạy phân tích 1 lần
  python main.py --schedule         # Chạy theo lịch
  python main.py --webui            # Web + schedule
  python main.py --webui-only       # Chỉ Web
  python main.py --force-run        # Bỏ qua check ngày giao dịch
  python main.py --dry-run          # Test không gửi notification
  ```

---

## Phase 3: Web UI Dashboard (Tuần 5-7)

> Mục tiêu: Web dashboard hoàn chỉnh giống repo gốc.

### 3.1 Backend API (FastAPI)

#### [NEW] `server.py`
- FastAPI server với các endpoint:
  - `POST /api/v1/analysis/analyze` — Trigger phân tích
  - `GET /api/v1/analysis/history` — Lịch sử phân tích
  - `GET /api/v1/market/overview` — Tổng quan thị trường
  - `GET /api/v1/stocks/search` — Tìm kiếm mã CK
  - `POST /api/v1/settings` — Cập nhật cấu hình
  - `GET /api/v1/usage/summary` — LLM usage statistics

### 3.2 Frontend (Vite + React + TypeScript)

#### [NEW] `apps/web/`
- Trang **Dashboard**: Decision Dashboard với bảng tổng hợp
- Trang **Phân tích**: Input mã CK → trigger phân tích → xem kết quả
- Trang **Đại bàn**: VN-Index, HNX-Index, gainers/losers, sector heatmap
- Trang **Lịch sử**: Xem lại các báo cáo cũ
- Trang **Cài đặt**: Quản lý API keys, stock list, notification channels
- **Dark/Light theme** với design token system
- **Responsive** cho mobile
- **Search autocomplete**: Tìm mã CK bằng code, tên, viết tắt (VNM → Vinamilk)

---

## Phase 4: Multi-Agent + Chat + Advanced (Tuần 8-10)

> Mục tiêu: Full agent system + interactive chat interface.

### 4.1 Multi-Agent Architecture

#### [NEW] `src/agents/*.py`
Pipeline 5 agents:
```
User query
    ↓
[Technical Agent] — Phân tích kỹ thuật (indicators, chart patterns)
    ↓
[Intel Agent] — Thu thập tin tức, sentiment, capital flow
    ↓
[Risk Agent] — Đánh giá rủi ro, cảnh báo
    ↓
[Specialist Agent] — Áp dụng strategy đã chọn
    ↓
[Decision Agent] — Tổng hợp → Decision Dashboard cuối cùng
```

### 4.2 Chat Interface (Agent 问股)

- Trang `/chat` trên Web UI
- Người dùng có thể hỏi tự nhiên: "Phân tích VNM bằng chiến lược MA Crossover"
- Streaming response (hiển thị tiến trình AI đang suy nghĩ)
- Lưu lịch sử hội thoại
- Bot commands: `/ask`, `/chat`, `/history`, `/strategies`

### 4.3 Portfolio & Backtest

- Quản lý danh mục đầu tư (mua/bán/P&L)
- Backtest: So sánh dự đoán AI vs thực tế (next-day verification)
- Export CSV/PDF

### 4.4 Docker Deployment

#### [NEW] `docker/`
- `Dockerfile` cho backend
- `docker-compose.yml` với services: app + (optional) postgres
- Environment variables qua `.env`

---

## Mapping: Repo Gốc → VN Version

| Component (Gốc - CN) | Thay thế (VN) | Ghi chú |
|---|---|---|
| Efinance | `vnstock` (VCI source) | Provider chuyên cho VN |
| AkShare | `vnstock` (KBS source) | Fallback source |
| Tushare | SSI FastConnect API | Optional, cần đăng ký |
| Pytdx | VNDirect API | Optional, cần đăng ký |
| Baostock | — | Bỏ (không cần) |
| Longbridge | — | Bỏ (HK/US only) |
| WeChat Push | — | Bỏ |
| Feishu Push | — | Bỏ |
| PushPlus / ServerChan | — | Bỏ |
| Telegram Push | Telegram Push | Giữ nguyên |
| Discord Push | Discord Push | Giữ nguyên |
| 均线金叉 (MA Golden Cross) | MA Crossover | Adapt |
| 缠论 (Chan Theory) | Support/Resistance | Thay thế |
| 波浪理论 (Elliott Wave) | Bollinger Bands | Thay thế |
| 多头趋势 (Bull Trend) | VN30 Momentum | Thay thế |
| A股 lịch nghỉ lễ | VN lịch nghỉ lễ (Tết, 30/4, 2/9...) | Adapt |
| 上证指数 / 深证成指 | VN-Index / HNX-Index / UPCOM-Index | Adapt |
| 板块 (sectors CN) | Ngành ICB Việt Nam | Adapt |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ (backend), TypeScript (frontend) |
| Data | `vnstock`, SSI API, VNDirect API |
| LLM Router | `litellm` |
| Web Framework | FastAPI |
| Frontend | Vite + React + TypeScript |
| Scheduling | GitHub Actions / APScheduler |
| Notification | python-telegram-bot, discord.py |
| Charts | matplotlib / plotly (backend), recharts (frontend) |
| Templates | Jinja2 |
| Deployment | Docker, GitHub Actions |

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Chi phí** | Zero-cost (GitHub Actions free tier + Gemini free API) |
| **Performance** | Phân tích 10 mã CK < 5 phút |
| **Reliability** | Fallback chain cho cả data sources lẫn LLM |
| **Security** | API keys trong .env / GitHub Secrets, không hardcode |
| **Maintenance** | YAML-based strategies, no-code addition |
| **Scale** | Single user, lên đến ~50 mã CK tự chọn |

---

## Decision Log

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Dùng `vnstock` làm data provider chính | Miễn phí, actively maintained, hỗ trợ HOSE/HNX/UPCOM, có sẵn API cho financial data |
| 2 | Giữ kiến trúc LiteLLM router | Plug-and-play API keys, học hỏi kiến trúc, hỗ trợ đa model |
| 3 | Chỉ Telegram + Discord | Đơn giản hoá, phù hợp personal use |
| 4 | Song ngữ VI/EN | Config `REPORT_LANGUAGE=vi|en` |
| 5 | 4 phases chia nhỏ | Mỗi phase có deliverable rõ ràng, có thể demo sớm |
| 6 | Thay strategies CN → VN-friendly | Bỏ 缠论/波浪 (quá phức tạp), thay bằng các indicator phổ biến hơn |
| 7 | Fallback chain cho data | Đảm bảo reliability: vnstock fail → SSI → VNDirect |
| 8 | GitHub Actions scheduling | Zero-cost, không cần server riêng |

---

## Verification Plan

### Automated Tests
```bash
# Unit tests cho data providers
pytest tests/test_data_provider.py -v

# Test LLM client (mock)
pytest tests/test_llm_client.py -v

# Test trading calendar
pytest tests/test_trading_calendar.py -v

# Integration test: full analysis pipeline
pytest tests/test_analyzer_integration.py -v

# Lint
flake8 src/ --max-line-length=120
```

### Manual Verification
- Phase 1: Chạy `python main.py` với 1 mã VNM → kiểm tra output
- Phase 2: Nhận được message trên Telegram/Discord sau khi phân tích
- Phase 3: Mở `http://localhost:8000` → thao tác trên Web UI
- Phase 4: Chat "Phân tích VNM bằng MA Crossover" → nhận streaming response

---

## Open Questions
_(Không có — scope đã được xác nhận)_

---

# 📋 VN Stock Daily Analysis — Cải Tiến & Điều Kiến Kiến Trúc

> **Tài liệu này tổng hợp các đề xuất cải tiến** cho dự án `vn_stock_daily_analysis`, dựa trên đánh giá kiến trúc và thực tế triển khai thị trường Việt Nam.
> 
> 📅 Cập nhật: `2026-01-22` | 🎯 Mục tiêu: Tăng độ ổn định, giảm chi phí, dễ bảo trì

## 🎯 Tổng Quan Cải Tiến

| Hạng mục | Trạng thái | Priority | Impact |
|----------|-----------|----------|--------|
| ✅ Symbol Validator | 🟢 Proposed | High | ⭐⭐⭐⭐⭐ |
| ✅ Circuit Breaker Handler | 🟢 Proposed | High | ⭐⭐⭐⭐ |
| ✅ Local Caching Layer | 🟢 Proposed | High | ⭐⭐⭐⭐⭐ |
| ✅ LLM Response Cache | 🟢 Proposed | Medium | ⭐⭐⭐⭐ |
| ✅ Degraded Mode for Agents | 🟢 Proposed | Medium | ⭐⭐⭐ |
| ✅ Health Check Endpoint | 🟢 Proposed | Low | ⭐⭐⭐ |
| ✅ Parallel Agent Execution | 🟡 Future | Low | ⭐⭐⭐ |

---

## 🧩 Module Mới Đề Xuất

### 1. `src/utils/validator.py` — Validation Mã Chứng Khoán VN

```python
"""
validator.py — Utility để validate và chuẩn hóa mã chứng khoán Việt Nam
"""
import re
from typing import Optional, Tuple
from enum import Enum

class Exchange(Enum):
    HOSE = "HO"
    HNX = "HN"
    UPCOM = "UP"

class VNStockValidator:
    """Validator cho mã chứng khoán Việt Nam"""
    
    # Pattern: ABC hoặc ABC.HO / ABC.HN / ABC.UP
    SYMBOL_PATTERN = re.compile(
        r'^([A-Z]{1,4})(?:\.(' + '|'.join([e.value for e in Exchange]) + r'))?$',
        re.IGNORECASE
    )
    
    # Danh sách mã đặc biệt (ETF, chứng quyền, trái phiếu...)
    SPECIAL_PREFIXES = ['E', 'F', 'CW', 'TP', 'CB']
    
    @classmethod
    def validate(cls, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate mã chứng khoán
        Returns: (is_valid, error_message)
        """
        symbol = symbol.strip().upper()
        
        if not symbol:
            return False, "Symbol cannot be empty"
        
        match = cls.SYMBOL_PATTERN.match(symbol)
        if not match:
            return False, f"Invalid VN stock format: {symbol}. Expected: VNM, FPT.HO, VCB.HN"
        
        code, exchange = match.groups()
        
        # Check special prefixes
        if any(code.startswith(prefix) for prefix in cls.SPECIAL_PREFIXES):
            return True, None  # Allow but log warning
        
        return True, None
    
    @classmethod
    def normalize(cls, symbol: str, default_exchange: Exchange = Exchange.HOSE) -> str:
        """
        Chuẩn hóa mã: vnm → VNM.HO, fpt.hn → FPT.HN
        """
        symbol = symbol.strip().upper()
        match = cls.SYMBOL_PATTERN.match(symbol)
        
        if not match:
            raise ValueError(f"Cannot normalize invalid symbol: {symbol}")
        
        code, exchange = match.groups()
        exchange = exchange or default_exchange.value
        
        return f"{code}.{exchange}"
    
    @classmethod
    def is_bluechip(cls, symbol: str) -> bool:
        """Kiểm tra mã có thuộc VN30/VN Diamond không"""
        VN30_LIST = {
            'VNM', 'VCB', 'VHM', 'VRE', 'VIC', 'HPG', 'FPT', 'MWG', 'TCB', 'MBB',
            'SSI', 'VND', 'HCM', 'GAS', 'PLX', 'POW', 'TPB', 'ACB', 'STB', 'BVH'
        }
        code = symbol.split('.')[0].upper()
        return code in VN30_LIST
```

---

### 2. `src/market/circuit_breaker.py` — Xử Lý Trần/Sàn

```python
"""
circuit_breaker.py — Xử lý logic giá trần/floor của HOSE/HNX/UPCOM
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class PriceLimitConfig:
    """Cấu hình biên độ giá theo sàn và nhóm cổ phiếu"""
    hose_bluechip: float = 0.07    # VN30: ±7%
    hose_normal: float = 0.10      # HOSE thường: ±10%
    hnx: float = 0.10              # HNX: ±10%
    upcom: float = 0.15            # UPCOM: ±15%

class CircuitBreakerHandler:
    """Xử lý cảnh báo và logic khi cổ phiếu chạm trần/sàn"""
    
    def __init__(self, config: Optional[PriceLimitConfig] = None):
        self.config = config or PriceLimitConfig()
        self._ref_prices: Dict[str, float] = {}
    
    def set_reference_price(self, symbol: str, ref_price: float):
        """Set giá tham chiếu (giá đóng cửa phiên trước)"""
        self._ref_prices[symbol.upper()] = ref_price
    
    def get_price_limits(self, symbol: str) -> tuple[float, float]:
        """Tính giá trần/floor cho mã"""
        symbol = symbol.upper()
        if symbol not in self._ref_prices:
            raise ValueError(f"Reference price not set for {symbol}")
        
        ref = self._ref_prices[symbol]
        code, exchange = symbol.split('.') if '.' in symbol else (symbol, 'HO')
        
        if exchange == 'HO':
            limit = self.config.hose_bluechip if self._is_bluechip(code) else self.config.hose_normal
        elif exchange == 'HN':
            limit = self.config.hnx
        else:
            limit = self.config.upcom
        
        ceiling = ref * (1 + limit)
        floor = ref * (1 - limit)
        
        round_unit = 50 if exchange == 'UP' else 100
        ceiling = round(ceiling / round_unit) * round_unit
        floor = round(floor / round_unit) * round_unit
        
        return ceiling, floor
    
    def check_limit_status(self, symbol: str, current_price: float) -> dict:
        """Kiểm tra trạng thái giá hiện tại so với trần/floor"""
        ceiling, floor = self.get_price_limits(symbol)
        
        status = {
            'symbol': symbol,
            'current_price': current_price,
            'ceiling': ceiling,
            'floor': floor,
            'is_limit_up': False,
            'is_limit_down': False,
            'distance_to_ceiling': None,
            'distance_to_floor': None,
            'warning': None
        }
        
        tolerance = 0.001
        if current_price >= ceiling * (1 - tolerance):
            status['is_limit_up'] = True
            status['warning'] = f"⚠️ {symbol} đang ở giá TRẦN ({ceiling:,.0f}đ) — Khó mua"
        elif current_price <= floor * (1 + tolerance):
            status['is_limit_down'] = True
            status['warning'] = f"⚠️ {symbol} đang ở giá SÀN ({floor:,.0f}đ) — Khó bán"
        else:
            status['distance_to_ceiling'] = round((ceiling - current_price) / current_price * 100, 2)
            status['distance_to_floor'] = round((current_price - floor) / current_price * 100, 2)
        
        return status
    
    def _is_bluechip(self, code: str) -> bool:
        VN30_CODES = {
            'VNM', 'VCB', 'VHM', 'VRE', 'VIC', 'HPG', 'FPT', 'MWG', 'TCB', 'MBB',
            'SSI', 'VND', 'HCM', 'GAS', 'PLX', 'POW', 'TPB', 'ACB', 'STB', 'BVH',
            'MSN', 'VJC', 'HPX', 'DCM', 'PVS', 'BIM', 'NT2', 'GVR', 'TCH', 'REE'
        }
        return code in VN30_CODES
```

---

### 3. `src/utils/cache.py` — Caching Layer Đa Cấp

```python
"""
cache.py — Caching system cho data provider và LLM responses
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps
import sqlite3
from contextlib import contextmanager

class CacheConfig:
    """Cấu hình cache"""
    CACHE_DIR = Path(".cache")
    DB_PATH = CACHE_DIR / "cache.db"
    
    TTL = {
        'historical_data': 3600,
        'realtime_quote': 300,
        'financial_report': 86400,
        'llm_response': 7200,
        'news_sentiment': 1800,
    }
    
    MAX_CACHE_SIZE_MB = 500

class LocalCache:
    """SQLite-based local cache với LRU eviction"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.config.CACHE_DIR.mkdir(exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    ttl INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created ON cache_entries(created_at)')
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self.config.DB_PATH))
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        raw = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        key = self._generate_key(prefix, *args, **kwargs)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                'SELECT value, created_at, ttl FROM cache_entries WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            value, created_at, ttl = row
            if time.time() - created_at > ttl:
                self.delete(key)
                return None
            
            conn.execute(
                'UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?',
                (time.time(), key)
            )
            
            return json.loads(value)
    
    def set(self, prefix: str, value: Any, ttl: Optional[int] = None, *args, **kwargs):
        key = self._generate_key(prefix, *args, **kwargs)
        ttl = ttl or self.config.TTL.get(prefix, 3600)
        
        with self._get_connection() as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO cache_entries 
                   (key, value, created_at, ttl, last_accessed) 
                   VALUES (?, ?, ?, ?, ?)''',
                (key, json.dumps(value, default=str), time.time(), ttl, time.time())
            )
    
    def delete(self, key: str):
        with self._get_connection() as conn:
            conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))

# Decorator để cache function calls
def cached(prefix: str, ttl: Optional[int] = None):
    def decorator(func: Callable):
        cache = LocalCache()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = cache.get(prefix, func.__name__, *args, **kwargs)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(prefix, result, ttl, func.__name__, *args, **kwargs)
            return result
        return wrapper
    return decorator
```

---

## 🔄 Cải Tiến Data Provider & Fallback Router

```python
# src/data_provider/fallback_router.py — Bổ sung retry + logging
import time
import logging
from typing import List, Optional, Callable
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class FallbackRouter:
    """Router với retry logic và circuit breaker pattern"""
    
    def __init__(self, providers: List[BaseDataProvider], max_retries: int = 3):
        self.providers = providers
        self.max_retries = max_retries
        self._failure_counts = {id(p): 0 for p in providers}
        self._circuit_open = {id(p): False for p in providers}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def execute_with_fallback(self, operation: str, *args, **kwargs) -> Any:
        last_error = None
        
        for provider in self.providers:
            provider_id = id(provider)
            if self._circuit_open.get(provider_id):
                continue
            
            try:
                method = getattr(provider, operation)
                result = method(*args, **kwargs)
                self._failure_counts[provider_id] = 0
                return result
                
            except Exception as e:
                last_error = e
                self._failure_counts[provider_id] += 1
                
                if self._failure_counts[provider_id] >= 5:
                    self._circuit_open[provider_id] = True
                continue
        
        raise RuntimeError(f"All providers failed for {operation}: {last_error}")
```

---

## 🏥 Health Check & Monitoring

### Health Check Endpoint

```python
# server.py — FastAPI health endpoint
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import time

app = FastAPI(title="VN Stock Analysis API")

class HealthStatus(BaseModel):
    status: str
    timestamp: float
    services: dict
    version: str

@app.get("/api/v1/health", response_model=HealthStatus)
async def health_check():
    checks = {}
    overall_status = "healthy"
    
    # Check data provider (VNStockProvider)
    # Check llm_router
    # Check trading_calendar
    # Check cache stats
    
    return HealthStatus(
        status=overall_status,
        timestamp=time.time(),
        services=checks,
        version="1.0.0"
    )
```

---

## ✅ Checklist Triển Khai Phase 1 (Đã Cập Nhật)

```markdown
## Phase 1 MVP Checklist

### 🔐 Setup & Configuration
- [ ] Tạo tài khoản vnstocks.com → lấy `VNSTOCK_API_KEY`
- [ ] Copy `.env.example` → `.env` và điền keys.
- [ ] Test connection với vnstock.

### 🧪 Testing Data Providers & Utils
- [ ] Test `VNStockValidator` với các mã CK khác nhau.
- [ ] Test `CircuitBreakerHandler` cảnh báo trần/sàn.
- [ ] Test `VNStockProvider` với fallback + local caching.

### 🤖 LLM Integration
- [ ] Test `LiteLLMClient` với prompt schema JSON rõ ràng.
- [ ] Verify caching response của LLM.
- [ ] Test fallback: set model sai → kiểm tra chuyển sang backup model.

### 📊 Core Analyzer MVP
- [ ] Chạy `python main.py --symbol VNM.HO --dry-run`
- [ ] Xử lý degraded mode (nếu API fail).
- [ ] Verify output có đủ: Thông số kĩ thuật, LLM result, cảnh báo rủi ro.

### 🧹 Code Quality
- [ ] Add type hints cho các function.
- [ ] Run linter (flake8) & Unit tests.
```

---

> 🎯 **Mục tiêu Week 1**: MVP chạy được `python main.py --symbol VNM.HO --dry-run` ổn định, có fallback, cache và in ra báo cáo text ở Terminal.
