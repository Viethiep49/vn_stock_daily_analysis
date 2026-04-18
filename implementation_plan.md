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

## Phase 1: Foundation — Data Provider + Core Analysis (Tuần 1-2) ✅

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

## Phase 2: Notification + Strategies + Scheduling (Tuần 3-4) ✅

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

## Phase 3: Web UI Dashboard (Tuần 5-7) 🔄

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

## Lộ trình phát triển đã đạt được

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| **Phase 1** | MVP: Data Provider + AI Analyzer + CLI | ✅ Hoàn thành |
| **Phase 2** | Notification + Strategies YAML + GitHub Actions | ✅ Hoàn thành |
| **Phase 3** | Web UI Dashboard (FastAPI + React) | 🔄 Đang triển khai (Streamlit ✅) |
| **Phase 4** | Multi-Agent + Chat Interface + Advanced | ⏳ Kế hoạch |

---

# 📋 VN Stock Daily Analysis — Cải Tiến & Điều Kiến Kiến Trúc

> **Tài liệu này tổng hợp các đề xuất cải tiến** cho dự án `vn_stock_daily_analysis`, dựa trên đánh giá kiến trúc và thực tế triển khai thị trường Việt Nam.

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

... (REST OF FILE KEPT AS IS)
