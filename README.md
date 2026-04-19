# 🇻🇳 VN Stock Daily Analysis Agent

Daily automated AI analysis for the Vietnamese stock market with notifications via Telegram / Discord.

> **Stack:** Python 3.11+ · vnstock v3.5+ · LiteLLM · FastAPI/Streamlit · GitHub Actions

---

## ✨ Features

| Feature | Status |
|-----------|-----------|
| Real-time data from HOSE/HNX (vnstock) | ✅ Phase 1 |
| Symbol Validation & Normalization | ✅ Phase 1 |
| Automatic Ceiling/Floor Price Warnings | ✅ Phase 1 |
| AI Analysis (Gemini/OpenAI via LiteLLM) | ✅ Phase 1 |
| Telegram Reports (Markdown) | ✅ Phase 2 |
| Discord Reports (Rich Embeds) | ✅ Phase 2 |
| Trading Strategies (YAML-based) | ✅ Phase 2 |
| Scheduled Automation (GitHub Actions) | ✅ Phase 2 |
| Web Dashboard (Streamlit) | 🔄 Phase 3 |
| Multi-Agent Analysis Pipeline | ⏳ Phase 4 |
| Watchlist Management | ⏳ Phase 4 |

---

## 🚀 Quick Start

### Prerequisites
- Python **3.11+**
- pip or uv

### Step 1 — Clone & Virtual Environment
```bash
git clone <repo-url>
cd vn_stock_daily_analysis

python3.11 -m venv venv
source venv/bin/activate       # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### Step 2 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Configuration
```bash
cp .env.example .env
# Open .env and fill in your API keys
```

---

## 📖 Documentation

Detailed documentation is available in the `docs/` directory:

### For Users
- [**Getting Started**](docs/user/getting-started.md): Installation and first run.
- [**Configuration Guide**](docs/user/configuration.md): Setting up LLMs and Notifications.
- [**Usage Guide**](docs/user/usage-guide.md): CLI commands and GitHub Actions.

### For Developers
- [**Architecture Overview**](docs/dev/architecture.md): How the system works.
- [**API Reference**](docs/dev/api-reference.md): Module and file breakdown.
- [**Strategy Customization**](docs/dev/strategy-customization.md): Creating your own trading strategies.
- [**Testing Guide**](docs/dev/testing.md): Running and writing tests.

---

## 💻 Usage

### Analyze a Single Symbol

```bash
# Analyze VNM, print to Terminal (dry-run)
python main.py --symbol VNM.HO --dry-run

# Analyze FPT and send to Telegram/Discord
python main.py --symbol FPT.HO
```

### Supported Symbol Formats
- `VNM` (Automatically adds `.HO`)
- `VNM.HO` (HoSE)
- `ACB.HN` (HNX)

---

## 🏗️ Project Structure

```
vn_stock_daily_analysis/
├── main.py                          # CLI Entry point
├── app.py                           # Streamlit Web Dashboard
├── src/
│   ├── core/                        # Core orchestrators
│   ├── data_provider/               # Market data sources
│   ├── market/                      # VN Market rules
│   ├── notifier/                    # Push notifications
│   ├── strategies/                  # YAML Strategies
│   └── utils/                       # Shared utilities
└── tests/                           # Unit & Integration tests
```

---

## 🤝 Contributing

Contributions are welcome! Please see [**CONTRIBUTING.md**](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License — see [LICENSE](./LICENSE) for details.
