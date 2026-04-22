"use client";

import { useState, useEffect, useRef } from "react";

// --- Animated Area Chart ---
function AreaChart({ data, color }: { data: { t: string; v: number }[]; color: string }) {
  const width = 600;
  const height = 160;
  const padding = { top: 10, right: 10, bottom: 30, left: 50 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const values = data.map((d) => d.v);
  const min = Math.min(...values) * 0.995;
  const max = Math.max(...values) * 1.005;
  const range = max - min;

  const toX = (i: number) => padding.left + (i / (data.length - 1)) * innerW;
  const toY = (v: number) => padding.top + innerH - ((v - min) / range) * innerH;

  const linePath = data
    .map((d, i) => `${i === 0 ? "M" : "L"} ${toX(i)} ${toY(d.v)}`)
    .join(" ");

  const areaPath =
    linePath +
    ` L ${toX(data.length - 1)} ${padding.top + innerH} L ${toX(0)} ${padding.top + innerH} Z`;

  const isUp = values[values.length - 1] >= values[0];
  const lineColor = isUp ? "#10B981" : "#EF4444";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      role="img"
      aria-label="Price chart"
    >
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
        <linearGradient id="gridGrad" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="rgba(255,255,255,0.03)" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.03)" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((t) => {
        const y = padding.top + t * innerH;
        const val = max - t * range;
        return (
          <g key={t}>
            <line
              x1={padding.left}
              y1={y}
              x2={padding.left + innerW}
              y2={y}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1"
            />
            <text
              x={padding.left - 6}
              y={y + 4}
              textAnchor="end"
              fontSize="9"
              fill="rgba(255,255,255,0.3)"
              fontFamily="JetBrains Mono, monospace"
            >
              {(val / 1000).toFixed(1)}k
            </text>
          </g>
        );
      })}

      {/* X-axis labels */}
      {data
        .filter((_, i) => i % Math.floor(data.length / 5) === 0)
        .map((d, i) => {
          const origIdx = i * Math.floor(data.length / 5);
          return (
            <text
              key={d.t}
              x={toX(origIdx)}
              y={height - 4}
              textAnchor="middle"
              fontSize="9"
              fill="rgba(255,255,255,0.3)"
              fontFamily="JetBrains Mono, monospace"
            >
              {d.t}
            </text>
          );
        })}

      {/* Area fill */}
      <path d={areaPath} fill="url(#areaGrad)" />

      {/* Line */}
      <path
        d={linePath}
        fill="none"
        stroke={lineColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Last point dot */}
      <circle
        cx={toX(data.length - 1)}
        cy={toY(values[values.length - 1])}
        r="4"
        fill={lineColor}
        stroke="#000"
        strokeWidth="2"
      />
    </svg>
  );
}

// --- Scorecard Row ---
function ScorecardRow({ name, score, signal, reason }: { name: string; score: number; signal: string; reason: string }) {
  const signalClass =
    signal === "BUY" ? "signal-buy" : signal === "SELL" ? "signal-sell" : "signal-hold";

  return (
    <div className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
      <div className="w-32 text-xs text-white/50 font-mono truncate">{name}</div>
      <div className="flex-1">
        <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${score}%`,
              background:
                score >= 70
                  ? "linear-gradient(90deg, #10B981, #34D399)"
                  : score >= 40
                  ? "linear-gradient(90deg, #F59E0B, #FCD34D)"
                  : "linear-gradient(90deg, #EF4444, #F87171)",
            }}
            role="progressbar"
            aria-valuenow={score}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${name} score: ${score}`}
          />
        </div>
      </div>
      <div className="text-xs font-mono text-white/60 w-8 text-right">{score}</div>
      <span className={signalClass}>{signal}</span>
    </div>
  );
}

// --- Generate mock chart data ---
function generateChartData(symbol: string, basePrice: number) {
  const data = [];
  let price = basePrice * 0.92;
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    price = price * (1 + (Math.random() - 0.47) * 0.025);
    data.push({
      t: `${d.getDate()}/${d.getMonth() + 1}`,
      v: Math.round(price),
    });
  }
  return data;
}

const DEMO_STOCKS = [
  {
    id: "vnm",
    symbol: "VNM",
    name: "Vinamilk",
    price: 69500,
    change: 2.34,
    composite: 87,
    signal: "BUY",
    sector: "FMCG",
    exchange: "HOSE",
    cards: [
      { name: "RSI Momentum", score: 72, signal: "BUY", reason: "RSI 58, uptrend" },
      { name: "MACD Cross", score: 81, signal: "BUY", reason: "Bullish crossover" },
      { name: "Volume Trend", score: 65, signal: "BUY", reason: "Volume tăng 1.3x" },
      { name: "Price Action", score: 78, signal: "BUY", reason: "Higher highs" },
      { name: "Risk Score", score: 30, signal: "SELL", reason: "P/E cao hơn ngành" },
    ],
  },
  {
    id: "fpt",
    symbol: "FPT",
    name: "FPT Corp",
    price: 128000,
    change: 4.12,
    composite: 91,
    signal: "BUY",
    sector: "Tech",
    exchange: "HOSE",
    cards: [
      { name: "RSI Momentum", score: 88, signal: "BUY", reason: "RSI 65, strong" },
      { name: "MACD Cross", score: 90, signal: "BUY", reason: "Strong divergence" },
      { name: "Volume Trend", score: 85, signal: "BUY", reason: "Volume đột biến" },
      { name: "Fundamental", score: 95, signal: "BUY", reason: "EPS tăng 25% YoY" },
      { name: "Risk Score", score: 55, signal: "HOLD", reason: "Định giá hợp lý" },
    ],
  },
  {
    id: "hpg",
    symbol: "HPG",
    name: "Hòa Phát Group",
    price: 27300,
    change: -1.08,
    composite: 42,
    signal: "HOLD",
    sector: "Steel",
    exchange: "HOSE",
    cards: [
      { name: "RSI Momentum", score: 38, signal: "SELL", reason: "RSI 42, bearish" },
      { name: "MACD Cross", score: 35, signal: "SELL", reason: "Bearish crossover" },
      { name: "Volume Trend", score: 55, signal: "HOLD", reason: "Volume bình thường" },
      { name: "Fundamental", score: 62, signal: "BUY", reason: "P/B thấp" },
      { name: "Risk Score", score: 45, signal: "HOLD", reason: "Ngành khó khăn" },
    ],
  },
];

export default function MarketSection() {
  const [activeStock, setActiveStock] = useState(0);
  const [chartData, setChartData] = useState<{ t: string; v: number }[]>([]);
  const [analyzing, setAnalyzing] = useState(false);

  const stock = DEMO_STOCKS[activeStock];

  useEffect(() => {
    setChartData(generateChartData(stock.symbol, stock.price));
  }, [activeStock]);

  const handleAnalyze = () => {
    setAnalyzing(true);
    setTimeout(() => setAnalyzing(false), 2000);
  };

  return (
    <section id="market" className="py-28 relative overflow-hidden" aria-label="Market Analysis Demo">
      {/* Background */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 50% 40% at 50% 100%, rgba(245,158,11,0.06) 0%, transparent 60%)",
        }}
        aria-hidden="true"
      />

      <div className="section-container relative z-10">
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card border border-amber-500/20 text-sm mb-4">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse-dot" aria-hidden="true" />
            <span className="text-amber-400 font-medium">Live Demo</span>
          </div>
          <h2 className="font-display text-4xl lg:text-5xl font-bold gradient-text-white">
            Phân Tích Thực Tế
          </h2>
          <p className="text-white/50 text-lg max-w-xl mx-auto">
            Xem cách hệ thống AI phân tích và đưa ra tín hiệu cho cổ phiếu Việt Nam
          </p>
        </div>

        {/* Stock selector */}
        <div className="flex flex-wrap gap-3 mb-6" role="tablist" aria-label="Stock selector">
          {DEMO_STOCKS.map((s, i) => (
            <button
              key={s.id}
              id={`stock-tab-${s.id}`}
              onClick={() => setActiveStock(i)}
              role="tab"
              aria-selected={i === activeStock}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer ${
                i === activeStock
                  ? "gradient-gold text-black shadow-lg"
                  : "glass-card text-white/60 hover:text-white"
              }`}
            >
              {s.symbol}
              <span className="ml-2 text-xs opacity-60">{s.sector}</span>
            </button>
          ))}
        </div>

        {/* Main demo card */}
        <div
          className="glass-card p-6 lg:p-8 space-y-6"
          role="tabpanel"
          aria-label={`${stock.symbol} analysis`}
        >
          {/* Stock header row */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl gradient-gold flex items-center justify-center font-display font-bold text-black text-sm">
                {stock.symbol.slice(0, 2)}
              </div>
              <div>
                <h3 className="font-display font-bold text-xl">{stock.symbol}</h3>
                <p className="text-white/40 text-sm">{stock.name} · {stock.exchange} · {stock.sector}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-2xl font-display font-bold">
                  {stock.price.toLocaleString("vi-VN")}đ
                </div>
                <div className={`text-sm font-medium ${stock.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {stock.change >= 0 ? "+" : ""}{stock.change.toFixed(2)}%
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-display font-bold gradient-text-gold">{stock.composite}</div>
                <div className="text-xs text-white/40">AI Score</div>
              </div>
              <span className={stock.signal === "BUY" ? "signal-buy" : stock.signal === "SELL" ? "signal-sell" : "signal-hold"}>
                {stock.signal}
              </span>
            </div>
          </div>

          {/* Chart */}
          <div className="glass-card-blue p-4 rounded-xl">
            {chartData.length > 0 && <AreaChart data={chartData} color="#10B981" />}
          </div>

          {/* Scorecard */}
          <div>
            <h4 className="text-sm font-semibold text-white/60 mb-3 font-display">AI SCORECARD BREAKDOWN</h4>
            <div className="space-y-0">
              {stock.cards.map((card) => (
                <ScorecardRow key={card.name} {...card} />
              ))}
            </div>
          </div>

          {/* Analyze button */}
          <div className="flex items-center gap-4">
            <button
              id="analyze-btn"
              onClick={handleAnalyze}
              disabled={analyzing}
              className={`btn-primary ${analyzing ? "opacity-70 cursor-not-allowed" : ""}`}
            >
              {analyzing ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Đang Phân Tích...
                </>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4" aria-hidden="true">
                    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
                    <path d="M12 2v3M12 19v3M2 12h3M19 12h3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  Chạy AI Analysis
                </>
              )}
            </button>
            <span className="text-xs text-white/30 font-mono">
              Kết quả sẽ gửi qua Telegram/Discord
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
