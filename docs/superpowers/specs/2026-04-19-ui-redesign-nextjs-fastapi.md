---
name: UI Redesign — Next.js + FastAPI
description: Redesign VN Stock Daily Analysis dashboard from Streamlit to Next.js frontend + FastAPI backend
type: project
date: 2026-04-19
status: approved
---

# UI Redesign: Next.js + FastAPI

## Goal

Replace the Streamlit dashboard with a professional, production-grade web app using Next.js (frontend) and FastAPI (backend). All existing Python analysis logic is preserved and exposed via REST API.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript |
| UI Components | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Backend | FastAPI (Python) |
| LLM Streaming | Server-Sent Events (SSE) |
| Deploy (FE) | Vercel |
| Deploy (BE) | Railway or Render |

## Architecture

```
Next.js (frontend)
    ↕ REST + SSE
FastAPI (api/main.py)
    ↕ imports
src/ (existing Python logic — unchanged)
```

The existing `src/` codebase (agents, scoring, notifiers, etc.) is **not modified**. FastAPI wraps it.

## Backend (FastAPI)

**File:** `api/main.py`

Endpoints:
- `POST /analyze` — triggers full analysis, returns JSON result (info, quote, scoring report, tech summary)
- `GET /analyze/stream` — SSE endpoint streaming LLM narrative token-by-token
- `GET /health` — health check

The `AnalyzerFactory` from `src/agents/factory.py` is reused directly.

## Frontend (Next.js)

**Directory:** `frontend/`

### Layout

```
┌─ Sidebar ──────┬─ Main ─────────────────────────────────┐
│ Stock search   │ Header: tên CP + giá + badge tín hiệu  │
│ Model select   ├──────────────┬─────────────────────────┤
│ Multi-agent    │ Candlestick  │ Score gauge + breakdown  │
│ [Analyze btn]  │ (Recharts)   │ (animated progress bars) │
│                ├──────────────┴─────────────────────────┤
│ Recent tickers │ AI Analysis (streaming markdown)        │
│                │ Tech indicators (card grid)             │
└────────────────┴─────────────────────────────────────────┘
```

### Key Pages / Components

- `app/page.tsx` — main dashboard page
- `components/StockHeader` — tên CP, giá, % thay đổi, signal badge (BUY/SELL/HOLD màu)
- `components/CandlestickChart` — Recharts OHLCV chart (30 ngày), với volume
- `components/ScorePanel` — composite score gauge + per-strategy progress bars
- `components/AIAnalysis` — streaming markdown render (SSE consumer)
- `components/TechGrid` — card grid cho các chỉ số kỹ thuật
- `components/Sidebar` — stock input, model picker, multi-agent toggle, analyze button

### Color scheme

- Nền trắng sạch (`#FFFFFF`, `#F9FAFB`)
- Accent xanh lá tài chính: `#00C853`
- BUY: `#00C853`, SELL: `#FF3D00`, HOLD: `#FFB300`
- Circuit breaker warning: badge đỏ nổi bật

## Data Flow

1. User nhập mã CP + nhấn Analyze
2. Frontend `POST /analyze` → FastAPI chạy analyzer → trả JSON
3. Frontend render StockHeader, ScorePanel, TechGrid từ JSON
4. Frontend mở SSE `/analyze/stream` → render AI narrative theo từng token

## Out of Scope

- Authentication / user accounts
- Database persistence (no history storage)
- Mobile-native app
- Real-time auto-refresh (manual trigger only)
