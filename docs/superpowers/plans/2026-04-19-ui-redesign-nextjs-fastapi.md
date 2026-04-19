# UI Redesign — Next.js + FastAPI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Streamlit dashboard với Next.js 14 frontend + FastAPI backend, giữ nguyên toàn bộ Python analysis logic.

**Architecture:** FastAPI wrap `src/` hiện có thành REST API. Next.js gọi API, render UI. SSE streaming cho LLM narrative. Streamlit `app.py` giữ nguyên song song.

**Tech Stack:** Next.js 14 (App Router) · TypeScript · Tailwind CSS · shadcn/ui · ApexCharts · FastAPI · Python 3.10+

**Design Tokens (from ui-ux-pro-max):**
- Primary: `#3B82F6` | Secondary: `#60A5FA` | CTA: `#F97316` | BG: `#F8FAFC`
- Profit: `#22C55E` | Loss: `#EF4444` | Warning: `#FFA500`
- Chart: Candlestick → `lightweight-charts` (TradingView) | Score → Gauge (ApexCharts)
- Effects: count-up animation, profit/loss color transitions, hover tooltips

---

## File Map

```
api/
  main.py          # FastAPI app — POST /analyze, GET /analyze/stream, GET /health
  schemas.py       # Pydantic request/response models
  requirements.txt # fastapi uvicorn python-dotenv (+ existing src deps)

frontend/
  app/
    page.tsx             # Main dashboard page
    layout.tsx           # Root layout, font, metadata
  components/
    Sidebar.tsx          # Stock input, model picker, multi-agent toggle, analyze btn
    StockHeader.tsx      # Tên CP + giá + % change + BUY/SELL/HOLD badge
    CandlestickChart.tsx # lightweight-charts OHLCV (30 ngày)
    ScorePanel.tsx       # ApexCharts gauge + per-strategy progress bars
    AIAnalysis.tsx       # SSE consumer, streaming markdown render
    TechGrid.tsx         # Card grid cho tech indicators
  lib/
    api.ts               # fetch wrappers cho /analyze và /analyze/stream
  types/
    index.ts             # TypeScript interfaces (AnalysisResult, ScoreCard, Quote, etc.)
  package.json
  tailwind.config.ts
  next.config.ts
```

---

## Task 1: FastAPI Backend

**Files:**
- Create: `api/main.py`
- Create: `api/schemas.py`

- [ ] **1.1** Tạo `api/schemas.py` — Pydantic models cho request/response:

```python
from pydantic import BaseModel
from typing import Optional, List, Any

class AnalyzeRequest(BaseModel):
    symbol: str
    model: Optional[str] = None
    use_agents: bool = False

class ScoreCardOut(BaseModel):
    strategy_name: str
    score: float
    signal: str
    reason: str

class AnalysisResponse(BaseModel):
    symbol: str
    status: str
    info: dict
    quote: dict
    tech_summary: Optional[str]
    circuit_breaker: Optional[dict]
    composite_score: Optional[float]
    final_signal: Optional[str]
    score_cards: Optional[List[ScoreCardOut]]
    llm_analysis: Optional[str]
    error: Optional[str]
```

- [ ] **1.2** Tạo `api/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
import json, asyncio

load_dotenv()

from api.schemas import AnalyzeRequest, AnalysisResponse
from src.agents.factory import AnalyzerFactory

app = FastAPI(title="VN Stock Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalysisResponse)
def analyze(req: AnalyzeRequest):
    analyzer = AnalyzerFactory.create(use_agents=req.use_agents)
    result = analyzer.analyze(req.symbol, model=req.model)
    
    report = result.get("report")
    return AnalysisResponse(
        symbol=req.symbol,
        status=result.get("status", "success"),
        info=result.get("info", {}),
        quote=result.get("quote", {}),
        tech_summary=result.get("tech_summary"),
        circuit_breaker=result.get("circuit_breaker"),
        composite_score=report.composite if report else None,
        final_signal=report.final_signal.value if report else None,
        score_cards=[
            {"strategy_name": c.strategy_name, "score": c.score,
             "signal": c.signal.value, "reason": c.reason}
            for c in report.cards
        ] if report else None,
        llm_analysis=result.get("llm_analysis"),
        error=result.get("error"),
    )

@app.get("/analyze/stream")
async def analyze_stream(symbol: str, model: str = None, use_agents: bool = False):
    async def event_generator():
        analyzer = AnalyzerFactory.create(use_agents=use_agents)
        result = analyzer.analyze(symbol, model=model)
        text = result.get("llm_analysis", "")
        for chunk in [text[i:i+50] for i in range(0, len(text), 50)]:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **1.3** Chạy test thủ công:
```bash
cd E:/project/vn_stock_daily_analysis
uvicorn api.main:app --reload --port 8000
# Mở http://localhost:8000/health → {"status":"ok"}
# POST /analyze với {"symbol":"VNM.HO"} → JSON response
```

- [ ] **1.4** Commit:
```bash
git add api/
git commit -m "feat(api): add FastAPI backend wrapping existing analyzer"
```

---

## Task 2: Next.js Project Scaffold

**Files:** Create `frontend/`

- [ ] **2.1** Scaffold project:
```bash
cd E:/project/vn_stock_daily_analysis
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
cd frontend
npm install apexcharts react-apexcharts lightweight-charts react-markdown
npx shadcn@latest init -d
npx shadcn@latest add button input select badge card separator
```

- [ ] **2.2** Tạo `frontend/types/index.ts`:

```typescript
export interface ScoreCard {
  strategy_name: string;
  score: number;
  signal: "BUY" | "SELL" | "HOLD";
  reason: string;
}

export interface AnalysisResult {
  symbol: string;
  status: string;
  info: { company_name?: string; industry?: string; exchange?: string };
  quote: { price?: number; change?: number; change_pct?: number; volume?: number; history?: OHLCBar[] };
  tech_summary?: string;
  circuit_breaker?: { warning?: string };
  composite_score?: number;
  final_signal?: "BUY" | "SELL" | "HOLD";
  score_cards?: ScoreCard[];
  llm_analysis?: string;
  error?: string;
}

export interface OHLCBar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}
```

- [ ] **2.3** Tạo `frontend/lib/api.ts`:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchAnalysis(
  symbol: string,
  model?: string,
  useAgents = false
) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, model, use_agents: useAgents }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function streamAnalysis(
  symbol: string,
  onChunk: (chunk: string) => void,
  onDone: () => void
) {
  const url = `${API_BASE}/analyze/stream?symbol=${encodeURIComponent(symbol)}`;
  const es = new EventSource(url);
  es.onmessage = (e) => {
    if (e.data === "[DONE]") { es.close(); onDone(); return; }
    const { chunk } = JSON.parse(e.data);
    onChunk(chunk);
  };
  return () => es.close();
}
```

- [ ] **2.4** Commit:
```bash
git add frontend/
git commit -m "feat(frontend): scaffold Next.js project with types and API client"
```

---

## Task 3: Sidebar Component

**Files:** Create `frontend/components/Sidebar.tsx`

- [ ] **3.1** Tạo `frontend/components/Sidebar.tsx`:

```tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const MODELS = [
  { label: "Default (.env)", value: "" },
  { label: "Gemma 4 26B (Free)", value: "openrouter/google/gemma-4-26b-a4b-it:free" },
  { label: "Nemotron 120B (Free)", value: "openrouter/nvidia/nemotron-3-super-120b-a12b:free" },
];

interface SidebarProps {
  onAnalyze: (symbol: string, model: string, useAgents: boolean) => void;
  loading: boolean;
}

export function Sidebar({ onAnalyze, loading }: SidebarProps) {
  const [symbol, setSymbol] = useState("VNM.HO");
  const [model, setModel] = useState("");
  const [useAgents, setUseAgents] = useState(false);

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-gray-200 p-4 flex flex-col gap-4">
      <h2 className="font-bold text-lg text-[#3B82F6]">VN Stock AI</h2>
      <div>
        <label className="text-sm font-medium text-gray-600">Mã cổ phiếu</label>
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="VNM.HO"
          className="mt-1"
        />
      </div>
      <div>
        <label className="text-sm font-medium text-gray-600">LLM Model</label>
        <Select value={model} onValueChange={setModel}>
          <SelectTrigger className="mt-1">
            <SelectValue placeholder="Default (.env)" />
          </SelectTrigger>
          <SelectContent>
            {MODELS.map((m) => (
              <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={useAgents} onChange={(e) => setUseAgents(e.target.checked)} />
        Multi-Agent Analysis
      </label>
      <Button
        onClick={() => onAnalyze(symbol, model, useAgents)}
        disabled={loading || !symbol}
        className="bg-[#F97316] hover:bg-orange-600 text-white"
      >
        {loading ? "Đang phân tích..." : "🚀 Phân tích"}
      </Button>
    </aside>
  );
}
```

- [ ] **3.2** Commit:
```bash
git add frontend/components/Sidebar.tsx
git commit -m "feat(frontend): add Sidebar component"
```

---

## Task 4: StockHeader Component

**Files:** Create `frontend/components/StockHeader.tsx`

- [ ] **4.1** Tạo `frontend/components/StockHeader.tsx`:

```tsx
import { Badge } from "@/components/ui/badge";
import { AnalysisResult } from "@/types";

const SIGNAL_COLORS = {
  BUY: "bg-[#22C55E] text-white",
  SELL: "bg-[#EF4444] text-white",
  HOLD: "bg-[#FFA500] text-white",
};

export function StockHeader({ result }: { result: AnalysisResult }) {
  const { info, quote, final_signal } = result;
  const price = (quote.price ?? 0) * 1000;
  const change = (quote.change ?? 0) * 1000;
  const pct = quote.change_pct ?? 0;
  const isUp = change >= 0;

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center gap-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{result.symbol}</h1>
        <p className="text-sm text-gray-500">{info.company_name} · {info.exchange} · {info.industry}</p>
      </div>
      <div className="ml-auto text-right">
        <p className="text-3xl font-bold text-gray-900">{price.toLocaleString("vi-VN")} đ</p>
        <p className={`text-sm font-medium ${isUp ? "text-[#22C55E]" : "text-[#EF4444]"}`}>
          {isUp ? "▲" : "▼"} {Math.abs(change).toLocaleString("vi-VN")} đ ({pct > 0 ? "+" : ""}{pct.toFixed(2)}%)
        </p>
      </div>
      {final_signal && (
        <Badge className={`text-base px-4 py-1 ${SIGNAL_COLORS[final_signal]}`}>
          {final_signal}
        </Badge>
      )}
      {result.circuit_breaker?.warning && (
        <Badge className="bg-red-600 text-white animate-pulse">{result.circuit_breaker.warning}</Badge>
      )}
    </div>
  );
}
```

- [ ] **4.2** Commit:
```bash
git add frontend/components/StockHeader.tsx
git commit -m "feat(frontend): add StockHeader component"
```

---

## Task 5: CandlestickChart Component

**Files:** Create `frontend/components/CandlestickChart.tsx`

> ui-ux-pro-max recommendation: Candlestick → `lightweight-charts` (TradingView)

- [ ] **5.1** Tạo `frontend/components/CandlestickChart.tsx`:

```tsx
"use client";
import { useEffect, useRef } from "react";
import { createChart, ColorType } from "lightweight-charts";
import { OHLCBar } from "@/types";

export function CandlestickChart({ data }: { data: OHLCBar[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;
    const chart = createChart(containerRef.current, {
      layout: { background: { type: ColorType.Solid, color: "#FFFFFF" }, textColor: "#374151" },
      grid: { vertLines: { color: "#F3F4F6" }, horzLines: { color: "#F3F4F6" } },
      width: containerRef.current.clientWidth,
      height: 300,
    });
    const series = chart.addCandlestickSeries({
      upColor: "#22C55E", downColor: "#EF4444",
      borderUpColor: "#22C55E", borderDownColor: "#EF4444",
      wickUpColor: "#22C55E", wickDownColor: "#EF4444",
    });
    series.setData(data.slice(-30));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [data]);

  return <div ref={containerRef} className="w-full h-[300px]" />;
}
```

- [ ] **5.2** Note: `quote.history` cần được expose từ FastAPI. Nếu chưa có, thêm vào `AnalysisResponse` và `api/main.py` để trả `result.get("history", [])`.

- [ ] **5.3** Commit:
```bash
git add frontend/components/CandlestickChart.tsx
git commit -m "feat(frontend): add CandlestickChart with lightweight-charts"
```

---

## Task 6: ScorePanel Component

**Files:** Create `frontend/components/ScorePanel.tsx`

> ui-ux-pro-max recommendation: Score → Gauge (ApexCharts)

- [ ] **6.1** Tạo `frontend/components/ScorePanel.tsx`:

```tsx
"use client";
import dynamic from "next/dynamic";
import { ScoreCard } from "@/types";

const ApexChart = dynamic(() => import("react-apexcharts"), { ssr: false });

const SIGNAL_BG = { BUY: "bg-green-100 text-green-800", SELL: "bg-red-100 text-red-800", HOLD: "bg-yellow-100 text-yellow-800" };

export function ScorePanel({ score, cards }: { score: number; cards: ScoreCard[] }) {
  const gaugeOptions = {
    chart: { type: "radialBar" as const },
    plotOptions: {
      radialBar: {
        startAngle: -135, endAngle: 135,
        dataLabels: {
          name: { fontSize: "14px", color: "#6B7280", offsetY: -10 },
          value: { fontSize: "28px", fontWeight: 700, color: "#111827", formatter: (v: number) => `${v}` },
        },
      },
    },
    colors: [score >= 60 ? "#22C55E" : score >= 40 ? "#FFA500" : "#EF4444"],
    labels: ["Score"],
  };

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <ApexChart type="radialBar" series={[score]} options={gaugeOptions} height={220} />
      <div className="mt-2 space-y-2">
        {cards.map((c) => (
          <div key={c.strategy_name} className="flex items-center gap-2 text-sm">
            <span className="w-28 truncate text-gray-600">{c.strategy_name}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all"
                style={{ width: `${c.score}%`, backgroundColor: c.signal === "BUY" ? "#22C55E" : c.signal === "SELL" ? "#EF4444" : "#FFA500" }}
              />
            </div>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SIGNAL_BG[c.signal]}`}>{c.signal}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **6.2** Commit:
```bash
git add frontend/components/ScorePanel.tsx
git commit -m "feat(frontend): add ScorePanel with ApexCharts gauge"
```

---

## Task 7: AIAnalysis Streaming Component

**Files:** Create `frontend/components/AIAnalysis.tsx`

- [ ] **7.1** Tạo `frontend/components/AIAnalysis.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { streamAnalysis } from "@/lib/api";

export function AIAnalysis({ symbol, trigger }: { symbol: string; trigger: number }) {
  const [text, setText] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!trigger) return;
    setText("");
    setDone(false);
    const close = streamAnalysis(
      symbol,
      (chunk) => setText((prev) => prev + chunk),
      () => setDone(true)
    );
    return close;
  }, [symbol, trigger]);

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 min-h-[200px]">
      <h3 className="font-semibold text-gray-700 mb-3">🤖 Phân tích AI</h3>
      <div className="prose prose-sm max-w-none text-gray-700">
        <ReactMarkdown>{text}</ReactMarkdown>
        {!done && text && <span className="inline-block w-2 h-4 bg-[#3B82F6] animate-pulse ml-1" />}
      </div>
    </div>
  );
}
```

- [ ] **7.2** Commit:
```bash
git add frontend/components/AIAnalysis.tsx
git commit -m "feat(frontend): add AIAnalysis SSE streaming component"
```

---

## Task 8: TechGrid Component

**Files:** Create `frontend/components/TechGrid.tsx`

- [ ] **8.1** Tạo `frontend/components/TechGrid.tsx`:

```tsx
export function TechGrid({ summary }: { summary: string }) {
  const lines = summary?.split("\n").filter(Boolean) ?? [];
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
      <h3 className="font-semibold text-gray-700 mb-3">📊 Chỉ số kỹ thuật</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {lines.map((line, i) => (
          <div key={i} className="bg-[#F8FAFC] rounded-lg px-3 py-2 text-xs text-gray-600 font-mono">{line}</div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **8.2** Commit:
```bash
git add frontend/components/TechGrid.tsx
git commit -m "feat(frontend): add TechGrid component"
```

---

## Task 9: Main Page Assembly

**Files:** Modify `frontend/app/page.tsx`, create `frontend/app/layout.tsx`

- [ ] **9.1** Tạo `frontend/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VN Stock Daily Analysis",
  description: "AI-powered Vietnam stock analysis",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className={`${inter.className} bg-[#F8FAFC]`}>{children}</body>
    </html>
  );
}
```

- [ ] **9.2** Tạo `frontend/app/page.tsx`:

```tsx
"use client";
import { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { StockHeader } from "@/components/StockHeader";
import { CandlestickChart } from "@/components/CandlestickChart";
import { ScorePanel } from "@/components/ScorePanel";
import { AIAnalysis } from "@/components/AIAnalysis";
import { TechGrid } from "@/components/TechGrid";
import { fetchAnalysis } from "@/lib/api";
import { AnalysisResult } from "@/types";

export default function Home() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamTrigger, setStreamTrigger] = useState(0);

  const handleAnalyze = async (symbol: string, model: string, useAgents: boolean) => {
    setLoading(true); setError(null);
    try {
      const data = await fetchAnalysis(symbol, model || undefined, useAgents);
      setResult(data);
      setStreamTrigger((t) => t + 1);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar onAnalyze={handleAnalyze} loading={loading} />
      <main className="flex-1 p-6 space-y-4">
        {error && <div className="bg-red-50 text-red-700 p-4 rounded-xl">{error}</div>}
        {!result && !loading && (
          <div className="flex items-center justify-center h-full text-gray-400">
            Nhập mã cổ phiếu và nhấn Phân tích để bắt đầu.
          </div>
        )}
        {result && result.status !== "failed" && (
          <>
            <StockHeader result={result} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <CandlestickChart data={result.quote.history ?? []} />
              {result.composite_score != null && result.score_cards && (
                <ScorePanel score={result.composite_score} cards={result.score_cards} />
              )}
            </div>
            <AIAnalysis symbol={result.symbol} trigger={streamTrigger} />
            {result.tech_summary && <TechGrid summary={result.tech_summary} />}
          </>
        )}
      </main>
    </div>
  );
}
```

- [ ] **9.3** Chạy frontend:
```bash
cd frontend
npm run dev
# Mở http://localhost:3000 — nhập mã CP, nhấn Phân tích
```

- [ ] **9.4** Commit:
```bash
git add frontend/app/
git commit -m "feat(frontend): assemble main dashboard page"
```

---

## Task 10: Expose OHLC History từ Backend

**Files:** Modify `api/main.py`, `api/schemas.py`

- [ ] **10.1** Kiểm tra `src/core/analyzer.py` — kết quả `analyze()` có trả `history` không. Nếu chưa, thêm vào `Analyzer.analyze()`:

```python
# Trong analyze(), sau khi fetch history:
history = self.router.get_history(normalized_symbol, limit=30)
result["history"] = [
    {"time": str(r.date), "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
    for r in history
]
```

- [ ] **10.2** Update `api/schemas.py` — thêm `history` vào `AnalysisResponse`:

```python
history: Optional[List[dict]] = None
```

- [ ] **10.3** Update `api/main.py` — truyền `history=result.get("history")` vào `AnalysisResponse(...)`.

- [ ] **10.4** Commit:
```bash
git add api/ src/core/analyzer.py
git commit -m "feat(api): expose OHLC history for candlestick chart"
```

---

## Task 11: Deploy Config

**Files:** Create `.env.example`, `frontend/.env.local.example`, `Procfile` hoặc `render.yaml`

- [ ] **11.1** Tạo `frontend/.env.local` (local dev):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **11.2** Tạo `Procfile` cho Railway (backend):
```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **11.3** Deploy frontend lên Vercel: set `NEXT_PUBLIC_API_URL` = Railway backend URL trong Vercel dashboard.

- [ ] **11.4** Update CORS trong `api/main.py` — thay `allow_origins` thành production domain:
```python
allow_origins=["http://localhost:3000", "https://your-app.vercel.app"],
```

- [ ] **11.5** Commit:
```bash
git add Procfile frontend/.env.local.example
git commit -m "chore: add deploy config for Railway + Vercel"
```

---

## Tóm tắt thứ tự thực hiện

1. Task 1 (FastAPI) → test `POST /analyze` local
2. Task 2 (Scaffold + types + api client)
3. Task 3–8 (Components — có thể song song)
4. Task 10 (OHLC history — cần trước khi test chart)
5. Task 9 (Assemble page + end-to-end test)
6. Task 11 (Deploy)
