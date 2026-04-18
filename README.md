# 🇻🇳 VN Stock Daily Analysis Agent

Hệ thống AI Agent tự động phân tích cổ phiếu thị trường chứng khoán Việt Nam hàng ngày, gửi báo cáo qua Telegram / Discord.

> **Stack:** Python 3.11+ · vnstock v3.5+ · LiteLLM · FastAPI · GitHub Actions

---

## ✨ Tính năng

| Tính năng | Trạng thái |
|-----------|-----------|
| Lấy dữ liệu giá thực từ HOSE/HNX | ✅ Phase 1 |
| Validate & chuẩn hóa mã CK | ✅ Phase 1 |
| Cảnh báo trần/sàn tự động | ✅ Phase 1 |
| Cache SQLite tránh rate-limit | ✅ Phase 1 |
| Phân tích AI (LiteLLM → Gemini/OpenAI/Ollama) | ✅ Phase 1 |
| Push báo cáo Telegram | ✅ Phase 2 |
| Push báo cáo Discord (Rich Embeds) | ✅ Phase 2 |
| Chiến lược YAML (MA, RSI, Volume...) | ✅ Phase 2 |
| Lập lịch tự động GitHub Actions | ✅ Phase 2 |
| Web Dashboard (FastAPI + React) | 🔜 Phase 3 |
| Multi-Agent analysis | 🔜 Phase 4 |

---

## 🚀 Cài đặt nhanh

### Yêu cầu
- Python **3.11+** (vnstock yêu cầu ≥3.10)
- pip hoặc uv

### Bước 1 — Clone & tạo môi trường ảo
```bash
git clone <repo-url>
cd vn_stock_daily_analysis

python3.11 -m venv venv
source venv/bin/activate       # macOS/Linux
# hoặc: venv\Scripts\activate  # Windows
```

### Bước 2 — Cài dependencies
```bash
pip install -r requirements.txt
```

### Bước 3 — Cấu hình môi trường
```bash
cp .env.example .env
# Mở file .env và điền API keys (xem hướng dẫn bên dưới)
```

---

## 🔑 Cấu hình API Keys

### `.env` — Tất cả biến môi trường

```env
# ========= LLM (bắt buộc ít nhất 1) =========
GEMINI_API_KEY=AIza...          # Google AI Studio → aistudio.google.com (miễn phí)
OPENAI_API_KEY=sk-...           # OpenAI Platform (trả phí)
ANTHROPIC_API_KEY=sk-ant-...    # Anthropic Console (trả phí)

# ========= Notification (tuỳ chọn) ===========
TELEGRAM_BOT_TOKEN=123456:ABC...  # Tạo bot tại @BotFather trên Telegram
TELEGRAM_CHAT_ID=-100...          # ID của chat/group muốn gửi tin

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# ========= Cấu hình LLM =====================
LLM_PRIMARY_MODEL=gemini/gemini-2.0-flash    # Model ưu tiên
LLM_BACKUP_MODEL=gemini/gemini-1.5-flash     # Model dự phòng khi lỗi
```

### Lấy API Key miễn phí

| Dịch vụ | Link | Ghi chú |
|---------|------|---------|
| **Gemini** (khuyên dùng) | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Miễn phí, mạnh |
| **vnstock** | [vnstocks.com](https://vnstocks.com) | Dữ liệu chứng khoán VN, nguồn KBS miễn phí |
| **Telegram Bot** | Nhắn `/newbot` tới @BotFather | Miễn phí |
| **Discord Webhook** | Server Settings → Integrations → Webhooks | Miễn phí |

---

## 💻 Cách sử dụng

### Chạy phân tích một mã

```bash
# Phân tích VNM, in ra Terminal (không gửi notification)
python main.py --symbol VNM.HO --dry-run

# Phân tích FPT và gửi lên Telegram/Discord
python main.py --symbol FPT.HO

# Phân tích HPG, buộc chạy dù hôm nay không phải ngày giao dịch
python main.py --symbol HPG --force-run --dry-run
```

### Định dạng mã chứng khoán được chấp nhận
```
VNM          → Vinamilk (HOSE), tự động thêm .HO
VNM.HO       → Vinamilk (HOSE) - format chuẩn
ACB.HN       → ACB (HNX)
SHB.HN       → SHB (HNX)
FPT          → FPT (HOSE)
```

### Output mẫu
```
==================================================
BÁO CÁO PHÂN TÍCH: VNM.HO
==================================================
🏢 Công ty: CTCP Sữa Việt Nam | Ngành:  | Sàn: HOSE
💰 Giá:    61,300đ  (+200đ / +0.33%)
📦 KL giao dịch: 3,115,500 cổ phiếu
📈 Kỹ thuật: MA5=62,420đ | MA20=61,850đ | KL hôm nay/TB20: 0.8x
--------------------------------------------------
🤖 LLM Analysis:
1. Xu hướng: VNM đang hồi phục nhẹ sau vùng hỗ trợ 60,000đ...
2. Rủi ro: Áp lực bán tại vùng 63,000đ, khối lượng thấp hơn TB...
3. Khuyến nghị: GIỮ — chờ xác nhận vượt kháng cự.
--------------------------------------------------
✅ Trạng thái: Hoàn thành
```

---

## 🏗️ Cấu trúc dự án

```
vn_stock_daily_analysis/
├── main.py                          # Entry point CLI
├── requirements.txt
├── .env.example                     # Mẫu cấu hình
├── implementation_plan.md           # Kế hoạch triển khai đầy đủ
│
├── src/
│   ├── core/
│   │   ├── analyzer.py              # Orchestrator chính
│   │   └── llm_client.py            # LiteLLM wrapper (Gemini/OpenAI/Ollama)
│   │
│   ├── data_provider/
│   │   ├── base.py                  # Abstract interface
│   │   ├── vnstock_provider.py      # 🔥 Data thực từ vnstock v3.5 (KBS)
│   │   └── fallback_router.py       # Retry + fallback logic
│   │
│   ├── market/
│   │   ├── circuit_breaker.py       # Cảnh báo giá trần/sàn HOSE/HNX/UPCOM
│   │   └── sector_mapping.py        # Mapping ngành ICB Việt Nam
│   │
│   ├── notifier/
│   │   ├── base.py                  # Abstract notifier
│   │   ├── telegram_bot.py          # Push Telegram (Markdown)
│   │   └── discord_bot.py           # Push Discord (Rich Embeds)
│   │
│   ├── strategies/                  # Chiến lược trading dạng YAML
│   │   ├── ma_crossover.yaml        # MA20 cắt MA50
│   │   ├── rsi_divergence.yaml      # RSI phân kỳ
│   │   ├── volume_breakout.yaml     # Đột phá khối lượng
│   │   ├── support_resistance.yaml  # Hỗ trợ / Kháng cự
│   │   ├── bollinger_bands.yaml     # Bollinger Bands
│   │   └── vn30_momentum.yaml       # Momentum VN30
│   │
│   └── utils/
│       ├── validator.py             # Validate mã CK
│       └── cache.py                 # SQLite local cache
│
├── tests/
│   ├── test_data_provider.py        # Unit tests data provider
│   ├── test_validator.py            # Unit tests validator
│   ├── test_circuit_breaker.py      # Unit tests circuit breaker
│   ├── test_analyzer.py             # Integration tests analyzer
│   └── test_notifier.py             # Unit tests notifiers
│
└── .github/
    └── workflows/
        └── daily_analysis.yml       # GitHub Actions cron job
```

---

## ⚙️ GitHub Actions — Tự động hóa hàng ngày

Workflow tại `.github/workflows/daily_analysis.yml` sẽ tự chạy vào **15:00 ICT** (08:00 UTC) các ngày trong tuần.

### Thiết lập GitHub Secrets
Vào **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Giá trị |
|--------|---------|
| `GEMINI_API_KEY` | API key từ Google AI Studio |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID nhận báo cáo |
| `DISCORD_WEBHOOK_URL` | Webhook Discord (tuỳ chọn) |

### Chạy thủ công trên GitHub
1. Vào tab **Actions** trên repository
2. Chọn workflow **VN Stock Daily Analysis**
3. Click **Run workflow** → nhập mã CK → Run

---

## 🧪 Chạy Unit Tests

```bash
source venv/bin/activate

# Chạy toàn bộ test suite
PYTHONPATH=. pytest tests/ -v

# Chạy từng nhóm test
PYTHONPATH=. pytest tests/test_validator.py -v
PYTHONPATH=. pytest tests/test_circuit_breaker.py -v
PYTHONPATH=. pytest tests/test_data_provider.py -v --timeout=15
PYTHONPATH=. pytest tests/test_notifier.py -v

# Kiểm tra code quality
flake8 src/ main.py --max-line-length=120
```

---

## 📈 Chiến lược Trading (YAML)

Các chiến lược được định nghĩa trong `src/strategies/*.yaml`. Mỗi file có:

```yaml
name: "MA Crossover"
description: "..."
indicators:
  - name: MA20
    type: SMA
    period: 20
parameters:
  fast_ma: 20
  slow_ma: 50
prompt_template: >
  Xem xét dữ liệu ... → Tín hiệu MUA/BÁN
```

Trong Phase 4, các chiến lược sẽ được inject vào LLM context để phân tích chuyên sâu hơn.

---

## 🗺️ Lộ trình phát triển

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| **Phase 1** | MVP: Data Provider + AI Analyzer + CLI | ✅ Hoàn thành |
| **Phase 2** | Notification + Strategies YAML + GitHub Actions | ✅ Hoàn thành |
| **Phase 3** | Web Dashboard (FastAPI + React) | 🔜 Kế hoạch |
| **Phase 4** | Multi-Agent + Chat Interface + Advanced | 🔜 Kế hoạch |

Chi tiết: xem [implementation_plan.md](./implementation_plan.md)

---

## 🤝 Đóng góp & Phát triển

```bash
# Setup dev environment
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install autopep8  # code formatter

# Sau khi chỉnh sửa code
autopep8 -i -a -a -r src/ main.py   # Auto-format
flake8 src/ main.py --max-line-length=120  # Lint check
PYTHONPATH=. pytest tests/ -v               # Run tests
```

---

## 📝 Giấy phép

MIT License — xem [LICENSE](./LICENSE) để biết thêm.
