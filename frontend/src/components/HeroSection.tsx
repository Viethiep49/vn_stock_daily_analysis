"use client";

import { useEffect, useRef, useState } from "react";

// --- Sparkline SVG Chart ---
function SparklineChart({
  data,
  color,
}: {
  data: number[];
  color: string;
}) {
  const width = 120;
  const height = 40;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");
  const areaPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" aria-hidden="true">
      <defs>
        <linearGradient id={`grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#grad-${color.replace("#", "")})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// --- Animated counter ---
function AnimatedPrice({ target, prefix = "", suffix = "" }: { target: number; prefix?: string; suffix?: string }) {
  const [value, setValue] = useState(target * 0.97);
  useEffect(() => {
    const step = (target - value) / 20;
    let current = target * 0.97;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { setValue(target); clearInterval(timer); }
      else setValue(current);
    }, 30);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);
  return (
    <span>{prefix}{value.toLocaleString("vi-VN", { maximumFractionDigits: 0 })}{suffix}</span>
  );
}

const TICKERS = [
  {
    id: "vnm",
    symbol: "VNM",
    name: "Vinamilk",
    price: 69500,
    change: +2.34,
    volume: "12.5M",
    color: "#10B981",
    signal: "BUY",
    data: [62, 64, 63, 66, 65, 68, 67, 69, 68, 70, 69, 69.5],
  },
  {
    id: "fpt",
    symbol: "FPT",
    name: "FPT Corp",
    price: 128000,
    change: +4.12,
    volume: "8.2M",
    color: "#3B82F6",
    signal: "BUY",
    data: [110, 112, 115, 113, 118, 120, 119, 122, 124, 126, 127, 128],
  },
  {
    id: "hpg",
    symbol: "HPG",
    name: "Hòa Phát",
    price: 27300,
    change: -1.08,
    volume: "25.1M",
    color: "#EF4444",
    signal: "HOLD",
    data: [30, 29, 28.5, 29, 27.5, 28, 27, 27.5, 27.8, 27.3, 27.1, 27.3],
  },
];

export default function HeroSection() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [livePrices, setLivePrices] = useState(TICKERS.map((t) => t.price));
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Simulate live price updates
  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setLivePrices((prev) =>
        prev.map((p) => {
          const delta = (Math.random() - 0.49) * p * 0.002;
          return Math.round(p + delta);
        })
      );
    }, 2000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  useEffect(() => {
    const t = setInterval(() => setActiveIdx((i) => (i + 1) % TICKERS.length), 3000);
    return () => clearInterval(t);
  }, []);

  const ticker = TICKERS[activeIdx];

  return (
    <section
      className="relative min-h-screen flex flex-col justify-center overflow-hidden gradient-hero-bg"
      aria-label="Hero Section"
    >
      {/* Grid background */}
      <div className="absolute inset-0 grid-bg opacity-40" aria-hidden="true" />

      {/* Ambient blobs */}
      <div
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)", filter: "blur(40px)" }}
        aria-hidden="true"
      />
      <div
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%)", filter: "blur(40px)" }}
        aria-hidden="true"
      />

      <div className="section-container relative z-10 pt-32 pb-20">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Copy */}
          <div className="space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card border border-amber-500/20 text-sm">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse-dot" aria-hidden="true" />
              <span className="text-amber-400 font-medium font-mono">LIVE · Powered by AI Agents</span>
            </div>

            {/* Headline */}
            <h1 className="font-display font-bold text-5xl lg:text-6xl leading-tight tracking-tight">
              <span className="gradient-text-white">Phân Tích</span>
              <br />
              <span className="shimmer-text">Cổ Phiếu VN</span>
              <br />
              <span className="gradient-text-white">Bằng AI</span>
            </h1>

            {/* Subheadline */}
            <p className="text-white/60 text-lg leading-relaxed max-w-md">
              Hệ thống multi-agent phân tích thị trường HOSE/HNX theo thời gian thực.
              Tín hiệu mua/bán tự động gửi qua Telegram & Discord.
            </p>

            {/* Trust micro-stats */}
            <div className="flex items-center gap-6">
              {[
                { value: "500+", label: "Mã CK" },
                { value: "99.9%", label: "Uptime" },
                { value: "<1s", label: "Latency" },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-2xl font-display font-bold gradient-text-gold">{stat.value}</div>
                  <div className="text-xs text-white/40 mt-0.5">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4">
              <button
                id="hero-primary-cta"
                className="btn-primary"
                onClick={() => document.getElementById("market")?.scrollIntoView({ behavior: "smooth" })}
              >
                <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4" aria-hidden="true">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="currentColor" />
                </svg>
                Thử Ngay Miễn Phí
              </button>
              <button
                id="hero-secondary-cta"
                className="btn-secondary"
                onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}
              >
                Xem Tính Năng
                <svg viewBox="0 0 24 24" fill="none" className="w-4 h-4" aria-hidden="true">
                  <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>

          {/* Right: Live Chart Card */}
          <div className="relative">
            <div className="absolute -inset-4 rounded-2xl" style={{ background: "radial-gradient(ellipse at center, rgba(245,158,11,0.05), transparent 70%)" }} aria-hidden="true" />

            {/* Main glass card */}
            <div className="glass-card p-6 space-y-5 relative animate-border-glow" role="region" aria-label="Live stock preview">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center font-mono font-bold text-sm"
                    style={{ background: `${ticker.color}20`, color: ticker.color }}
                  >
                    {ticker.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <div className="font-display font-semibold text-base">{ticker.symbol}</div>
                    <div className="text-xs text-white/40">{ticker.name}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={ticker.signal === "BUY" ? "signal-buy" : ticker.signal === "SELL" ? "signal-sell" : "signal-hold"}>
                    {ticker.signal}
                  </span>
                  <span className="w-2 h-2 rounded-full animate-pulse-dot" style={{ background: ticker.color }} aria-hidden="true" />
                  <span className="text-xs text-white/40 font-mono">LIVE</span>
                </div>
              </div>

              {/* Price */}
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-3xl font-display font-bold tracking-tight">
                    <AnimatedPrice target={livePrices[activeIdx]} suffix="đ" />
                  </div>
                  <div className={`text-sm font-medium mt-1 ${ticker.change > 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {ticker.change > 0 ? "+" : ""}{ticker.change.toFixed(2)}%
                    <span className="text-white/30 ml-2">Vol: {ticker.volume}</span>
                  </div>
                </div>
                <div className="w-32 h-12">
                  <SparklineChart data={ticker.data} color={ticker.color} />
                </div>
              </div>

              {/* Ticker switcher dots */}
              <div className="flex items-center gap-2 pt-1">
                {TICKERS.map((t, i) => (
                  <button
                    key={t.id}
                    id={`ticker-dot-${t.id}`}
                    onClick={() => setActiveIdx(i)}
                    className={`h-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                      i === activeIdx ? "w-6 bg-amber-400" : "w-1.5 bg-white/20"
                    }`}
                    aria-label={`Switch to ${t.symbol}`}
                    aria-pressed={i === activeIdx}
                  />
                ))}
                <span className="text-xs text-white/30 ml-auto font-mono">Auto-switch</span>
              </div>
            </div>

            {/* Floating mini cards */}
            <div
              className="absolute -top-6 -right-6 glass-card px-4 py-3 animate-float"
              style={{ animationDelay: "0s" }}
              aria-hidden="true"
            >
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-emerald-500/20 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true">
                    <path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div>
                  <div className="text-xs font-semibold text-emerald-400">AI Signal</div>
                  <div className="text-xs text-white/40">BUY · Score 87/100</div>
                </div>
              </div>
            </div>

            <div
              className="absolute -bottom-4 -left-4 glass-card px-4 py-3 animate-float"
              style={{ animationDelay: "2s" }}
              aria-hidden="true"
            >
              <div className="flex items-center gap-2">
                <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5 text-blue-400" aria-hidden="true">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div>
                  <div className="text-xs font-semibold text-blue-400">Bảo Mật</div>
                  <div className="text-xs text-white/40">SSL · E2E Encrypted</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2" aria-hidden="true">
        <span className="text-xs text-white/30">Cuộn xuống</span>
        <div className="w-5 h-8 rounded-full border border-white/10 flex items-start justify-center pt-1.5">
          <div className="w-1 h-2 rounded-full bg-amber-400 animate-bounce" />
        </div>
      </div>
    </section>
  );
}
