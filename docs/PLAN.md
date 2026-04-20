# Implementation Plan: UI Redesign (Next.js + FastAPI)

This plan outlines the steps to migrate the VN Stock Daily Analysis dashboard from Streamlit to a production-grade Next.js frontend and FastAPI backend.

## 1. Project Structure

```text
vn_stock_daily_analysis/
├── api/            # FastAPI Backend
│   ├── main.py     # API entry point
│   └── utils/      # API helpers
├── frontend/       # Next.js Frontend
│   ├── app/        # App Router pages
│   ├── components/ # Shared components
│   ├── lib/        # Hooks and utils
│   └── styles/     # Tailwind configurations
└── src/            # Existing Python logic (unchanged)
```

## 2. Phase 1: Backend Setup (FastAPI)
- [x] Initialize `api/main.py`.
- [x] Implement `POST /analyze`:
    - Integrate with `AnalyzerFactory` from `src/agents/factory.py`.
    - Return analysis JSON (quote, score, tech indicators).
- [x] Implement `GET /analyze/stream`:
    - Setup Server-Sent Events (SSE).
    - Stream LLM narrative from the analyzer.
- [x] Implement `GET /health` for monitoring.
- [x] Verify backend independently using `curl` or FastAPI Docs.

## 3. Phase 2: Frontend Foundation
- [x] Initialize Next.js 14 project in `frontend/` (TypeScript, Tailwind, App Router).
- [x] Install dependencies: `lucide-react`, `recharts`, `framer-motion`, `shadcn/ui` components.
- [x] Setup Design System (HSL color palette, Typography) based on `ui-ux-pro-max`.
- [x] Create layout wrapper with Sidebar and Header.

## 4. Phase 3: Core Components Implementation
- [x] **Sidebar**: Stock input, Model selection, Multi-agent toggle.
- [x] **StockHeader**: Real-time-ish price updates and signal badges.
- [x] **ScorePanel**: Composite score gauge and strategy progress bars (animated).
- [x] **CandlestickChart**: Recharts implementation for OHLCV data.
- [x] **AIAnalysis**: Markdown renderer with SSE streaming support.
- [ ] **TechGrid**: Dynamic card grid for technical indicators.

## 5. Phase 4: Integration & Optimization
- [x] Connect Frontend to FastAPI endpoints.
- [x] Implement state management (React Context or simple `useState/useEffect`) for analysis flow.
- [ ] Add loading skeletons and error handling.
- [ ] Performance profiling (Lighthouse check).

## 6. Verification & Deployment
- [ ] Run `python .agent/scripts/checklist.py` for final audit.
- [ ] Final UI/UX review against `ui-ux-pro-max` guidelines.
- [ ] Deploy backend (Railway/Render) and frontend (Vercel).

---

## 🛑 User Approval Required

Do you approve this plan?
- **Y**: Proceed to Phase 2 (Implementation).
- **N**: Let me know which parts need modification.
