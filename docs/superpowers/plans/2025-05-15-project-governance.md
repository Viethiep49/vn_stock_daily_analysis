# Task 7: Project Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `CONTRIBUTING.md` and update `README.md` to English with documentation links.

**Architecture:** Documentation and Governance files.

**Tech Stack:** Markdown.

---

### Task 7.1: Create CONTRIBUTING.md

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create CONTRIBUTING.md with PR rules and coding standards**

```markdown
# Contributing to VN Stock Daily Analysis

Thank you for your interest in contributing to this project!

## Pull Request Process

1. **Create an Issue:** Before starting any work, please open an issue to discuss your proposed changes.
2. **Branching:** Create a new branch for your feature or bugfix (e.g., `feat/my-feature` or `fix/issue-id`).
3. **Tests:** Ensure all tests pass and add new tests for your changes.
4. **Pull Request:** Open a PR against the `main` branch. Provide a clear description of the changes.
5. **Review:** Wait for feedback and address any review comments.

## Coding Standards

- **Language:** Python 3.11+.
- **Formatting:** Follow PEP 8. Use `autopep8` or `black` for formatting.
- **Linting:** Code must pass `flake8` checks. Max line length is 120.
- **Naming:** Use `snake_case` for functions/variables and `PascalCase` for classes.
- **Documentation:** Use docstrings for all public functions, classes, and modules.
- **Types:** Use type hints for function arguments and return values.

## Testing Guidelines

- Use `pytest` for all tests.
- Place tests in the `tests/` directory.
- Aim for high test coverage for new logic.
- Run tests with: `PYTHONPATH=. pytest tests/ -v`

## Project Structure

- `src/core/`: Orchestration and core logic.
- `src/data_provider/`: Data fetching interfaces.
- `src/market/`: Market-specific logic (circuit breakers, sector mapping).
- `src/notifier/`: Notification bots (Telegram, Discord).
- `src/strategies/`: YAML-based trading strategies.
- `src/utils/`: Shared utilities and validators.
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add contributing guide"
```

### Task 7.2: Update README.md to English and Add Documentation Links

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Translate README.md to English and add Documentation section**

```markdown
# 🇻🇳 VN Stock Daily Analysis Agent

Daily automated AI analysis for the Vietnamese stock market with notifications via Telegram / Discord.

> **Stack:** Python 3.11+ · vnstock v3.5+ · LiteLLM · FastAPI · GitHub Actions

---

## ✨ Features

| Feature | Status |
|-----------|-----------|
| Real-time data fetching from HOSE/HNX | ✅ Phase 1 |
| Symbol validation & normalization | ✅ Phase 1 |
| Automated ceiling/floor alerts | ✅ Phase 1 |
| SQLite caching to avoid rate-limits | ✅ Phase 1 |
| AI Analysis (LiteLLM → Gemini/OpenAI/Ollama) | ✅ Phase 1 |
| Telegram notification push | ✅ Phase 2 |
| Discord notification push (Rich Embeds) | ✅ Phase 2 |
| YAML Strategies (MA, RSI, Volume...) | ✅ Phase 2 |
| GitHub Actions scheduling | ✅ Phase 2 |
| Web Dashboard (FastAPI + React) | 🔜 Phase 3 |
| Multi-Agent analysis | ✅ Done |
| Agent Skills (Markdown) | ✅ Done |

---

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

### User Guides
- [Getting Started](docs/user/getting-started.md)
- [Configuration Guide](docs/user/configuration.md)
- [Usage Guide](docs/user/usage-guide.md)

### Developer Guides
- [Architecture Overview](docs/dev/architecture.md)
- [API Reference](docs/dev/api-reference.md)
- [Testing Guide](docs/dev/testing.md)
- [Strategy Customization](docs/dev/strategy-customization.md)

---

## 🚀 Quick Start

### Requirements
- Python **3.11+** (vnstock requires ≥3.10)
- pip or uv

### Step 1 — Clone & Create Virtual Environment
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

### Step 3 — Environment Configuration
```bash
cp .env.example .env
# Open .env and fill in your API keys (see instructions below)
```

---

## 🔑 API Keys Configuration

### `.env` — All Environment Variables

```env
# ========= LLM (at least 1 required) =========
GEMINI_API_KEY=AIza...          # Google AI Studio → aistudio.google.com (free)
OPENAI_API_KEY=sk-...           # OpenAI Platform (paid)
ANTHROPIC_API_KEY=sk-ant-...    # Anthropic Console (paid)

# ========= Notification (optional) ===========
TELEGRAM_BOT_TOKEN=123456:ABC...  # Create bot via @BotFather on Telegram
TELEGRAM_CHAT_ID=-100...          # Chat/Group ID to send messages

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# ========= LLM Configuration =====================
LLM_PRIMARY_MODEL=gemini/gemini-2.0-flash    # Primary model
LLM_BACKUP_MODEL=gemini/gemini-1.5-flash     # Backup model on error
```

### Getting Free API Keys

| Service | Link | Notes |
|---------|------|---------|
| **Gemini** (Recommended) | [aistudio.google.com](https://aistudio.google.com/app/apikey) | Free, powerful |
| **vnstock** | [vnstocks.com](https://vnstocks.com) | VN stock data, KBS source is free |
| **Telegram Bot** | Message `/newbot` to @BotFather | Free |
| **Discord Webhook** | Server Settings → Integrations → Webhooks | Free |

---

## 💻 Usage

### Analyze a Single Symbol

```bash
# Analyze VNM, print to Terminal (no notifications)
python main.py --symbol VNM.HO --dry-run

# Analyze FPT and send to Telegram/Discord
python main.py --symbol FPT.HO

# Analyze HPG, force run even if today is not a trading day
python main.py --symbol HPG --force-run --dry-run
```

### Run with Multi-Agent Structure (Deep Dive)
```bash
# Analyze FPT with 3 Agents (Technical, Risk, Decision)
python main.py --symbol FPT --agents

# Analyze with specialized skills/strategies
python main.py --symbol HPG --agents --skill CANSLIM
```

See details in [docs/AGENTS.md](./docs/AGENTS.md).

### Accepted Symbol Formats
```
VNM          → Vinamilk (HOSE), automatically adds .HO
VNM.HO       → Vinamilk (HOSE) - standard format
ACB.HN       → ACB (HNX)
SHB.HN       → SHB (HNX)
FPT          → FPT (HOSE)
```

### Example Output
```
==================================================
ANALYSIS REPORT: VNM.HO
==================================================
🏢 Company: CTCP Sữa Việt Nam | Industry:  | Exchange: HOSE
💰 Price:    61,300 VND (+200 VND / +0.33%)
📦 Volume: 3,115,500 shares
📈 Technical: MA5=62,420 VND | MA20=61,850 VND | Volume today/Avg20: 0.8x
--------------------------------------------------
🤖 LLM Analysis:
1. Trend: VNM is recovering slightly after finding support at 60,000 VND...
2. Risks: Selling pressure near 63,000 VND, volume lower than average...
3. Recommendation: HOLD — wait for confirmation above resistance.
--------------------------------------------------
✅ Status: Completed
```

---

## 🏗️ Project Structure

```
vn_stock_daily_analysis/
├── main.py                          # CLI Entry point
├── requirements.txt
├── .env.example                     # Configuration template
├── implementation_plan.md           # Full implementation plan
│
├── src/
│   ├── core/
│   │   ├── analyzer.py              # Main Orchestrator
│   │   └── llm_client.py            # LiteLLM wrapper (Gemini/OpenAI/Ollama)
│   │
│   ├── data_provider/
│   │   ├── base.py                  # Abstract interface
│   │   ├── vnstock_provider.py      # 🔥 Real data from vnstock v3.5 (KBS)
│   │   └── fallback_router.py       # Retry + fallback logic
│   │
│   ├── market/
│   │   ├── circuit_breaker.py       # Price limit alerts (HOSE/HNX/UPCOM)
│   │   └── sector_mapping.py        # Vietnam ICB sector mapping
│   │
│   ├── notifier/
│   │   ├── base.py                  # Abstract notifier
│   │   ├── telegram_bot.py          # Telegram push (Markdown)
│   │   └── discord_bot.py           # Discord push (Rich Embeds)
│   │
│   ├── strategies/                  # YAML-based trading strategies
│   │   ├── ma_crossover.yaml        # MA20 crosses MA50
│   │   ├── rsi_divergence.yaml      # RSI divergence
│   │   ├── volume_breakout.yaml     # Volume breakout
│   │   ├── support_resistance.yaml  # Support / Resistance
│   │   ├── bollinger_bands.yaml     # Bollinger Bands
│   │   └── vn30_momentum.yaml       # VN30 Momentum
│   │
│   └── utils/
│       ├── validator.py             # Symbol validator
│       └── cache.py                 # SQLite local cache
│
├── tests/
│   ├── test_data_provider.py        # Data provider unit tests
│   ├── test_validator.py            # Validator unit tests
│   ├── test_circuit_breaker.py      # Circuit breaker unit tests
│   ├── test_analyzer.py             # Analyzer integration tests
│   └── test_notifier.py             # Notifier unit tests
│
└── .github/
    └── workflows/
        └── daily_analysis.yml       # GitHub Actions cron job
```

---

## ⚙️ GitHub Actions — Daily Automation

The workflow at `.github/workflows/daily_analysis.yml` runs at **15:00 ICT** (08:00 UTC) on weekdays.

### Set up GitHub Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|--------|---------|
| `GEMINI_API_KEY` | API key from Google AI Studio |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Chat ID for reports |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (optional) |

### Manual Run on GitHub
1. Go to the **Actions** tab on the repository
2. Select the **VN Stock Daily Analysis** workflow
3. Click **Run workflow** → enter symbol → Run

---

## 🧪 Running Unit Tests

```bash
source venv/bin/activate

# Run full test suite
PYTHONPATH=. pytest tests/ -v

# Run specific test groups
PYTHONPATH=. pytest tests/test_validator.py -v
PYTHONPATH=. pytest tests/test_circuit_breaker.py -v
PYTHONPATH=. pytest tests/test_data_provider.py -v --timeout=15
PYTHONPATH=. pytest tests/test_notifier.py -v

# Check code quality
flake8 src/ main.py --max-line-length=120
```

---

## 📈 Trading Strategies (YAML)

Strategies are defined in `src/strategies/*.yaml`. Each file contains:

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
  Analyze data ... → BUY/SELL Signal
```

In Phase 4, strategies are injected into the LLM context for deeper analysis.

---

## 🗺️ Roadmap

| Phase | Content | Status |
|-------|----------|-----------|
| **Phase 1** | MVP: Data Provider + AI Analyzer + CLI | ✅ Completed |
| **Phase 2** | Notification + Strategies YAML + GitHub Actions | ✅ Completed |
| **Phase 3** | Web Dashboard (FastAPI + React) | 🔜 Planned |
| **Phase 4** | Multi-Agent + Skills + Advanced Analysis | ✅ Completed |

Details: see [implementation_plan.md](./implementation_plan.md)

---

## 🤝 Contributing & Development

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

```bash
# Setup dev environment
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install autopep8  # code formatter

# After editing code
autopep8 -i -a -a -r src/ main.py   # Auto-format
flake8 src/ main.py --max-line-length=120  # Lint check
PYTHONPATH=. pytest tests/ -v               # Run tests
```

---

## 📝 License

MIT License — see [LICENSE](./LICENSE) for more details.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update readme to english and add doc links"
```
