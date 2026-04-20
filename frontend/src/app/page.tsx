"use client";

import React, { useState, useEffect } from "react";
import { Search, TrendingUp, Cpu, Activity, Info, AlertTriangle, CheckCircle2, LayoutGrid, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { AnalysisResult } from "@/types/analysis";
import { CandlestickChart } from "@/components/CandlestickChart";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";

// Placeholder components - will be moved to individual files
const Sidebar = ({ onAnalyze, loading }: { onAnalyze: (s: string) => void, loading: boolean }) => {
  const [symbol, setSymbol] = useState("VNM");
  return (
    <div className="w-80 border-r border-white/5 bg-black/20 p-6 flex flex-col gap-8 h-screen sticky top-0">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
          <TrendingUp className="text-white w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold tracking-tight">VN Stock <span className="text-blue-500">AI</span></h1>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Mã Chứng Khoán</label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full bg-zinc-900/50 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all font-medium uppercase"
            placeholder="Ví dụ: VNM, FPT..."
          />
        </div>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Cấu Hình</label>
        <div className="space-y-2">
           <button className="w-full glass-panel h-12 rounded-xl flex items-center justify-between px-4 text-sm font-medium hover:bg-white/5 transition-colors">
              <span className="flex items-center gap-2 text-zinc-400"><Cpu className="w-4 h-4" /> Model</span>
              <span className="text-blue-400">Gemma 4 (Free)</span>
           </button>
           <button className="w-full glass-panel h-12 rounded-xl flex items-center justify-between px-4 text-sm font-medium hover:bg-white/5 transition-colors">
              <span className="flex items-center gap-2 text-zinc-400"><Activity className="w-4 h-4" /> Multi-Agent</span>
              <span className="text-emerald-500">Enabled</span>
           </button>
        </div>
      </div>

      <button 
        onClick={() => onAnalyze(symbol)}
        disabled={loading}
        className={cn(
          "mt-auto w-full h-14 rounded-2xl bg-blue-600 font-bold shadow-xl shadow-blue-900/20 hover:bg-blue-500 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-50 disabled:pointer-events-none",
          loading && "animate-pulse"
        )}
      >
        {loading ? "Đang phân tích..." : "Bắt Đầu Phân Tích"}
      </button>
    </div>
  );
};

const Header = ({ result }: { result: AnalysisResult | null }) => {
  if (!result) return (
    <div className="h-20 border-b border-white/5 px-8 flex items-center justify-between">
      <div className="text-zinc-500 text-sm italic">Chọn một mã chứng khoán để bắt đầu...</div>
    </div>
  );

  const isUp = result.quote.change >= 0;

  return (
    <div className="h-24 border-b border-white/5 px-8 flex items-center justify-between bg-black/20 backdrop-blur-sm">
      <div className="flex items-center gap-6">
        <div>
          <div className="text-3xl font-black tracking-tighter uppercase">{result.symbol}</div>
          <div className="text-xs font-medium text-zinc-500 uppercase">{result.info.company_name}</div>
        </div>
        <div className="h-10 w-px bg-white/10" />
        <div>
          <div className="text-2xl font-bold tracking-tight">{(result.quote.last_price).toLocaleString()} <span className="text-xs text-zinc-500 font-medium">VND</span></div>
          <div className={cn("text-xs font-bold flex items-center gap-1", isUp ? "text-emerald-500" : "text-red-500")}>
            {isUp ? "▲" : "▼"} {Math.abs(result.quote.change).toFixed(2)} ({isUp ? "+" : ""}{result.quote.percent_change.toFixed(2)}%)
          </div>
        </div>
      </div>
      
      <div className={cn(
        "px-6 py-2 rounded-full border font-black text-sm uppercase tracking-widest",
        result.opinion.signal.includes("BUY") ? "signal-buy" : 
        result.opinion.signal.includes("SELL") ? "signal-sell" : "signal-hold"
      )}>
        {result.opinion.signal}
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamText, setStreamText] = useState("");

  const handleAnalyze = async (symbol: string) => {
    setLoading(true);
    setResult(null);
    setHistory([]);
    setStreamText("");
    
    try {
      // Parallel fetch analyze and history
      const [analysisRes, historyRes] = await Promise.all([
        fetch("http://localhost:8000/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbol, use_agents: true })
        }),
        fetch(`http://localhost:8000/history?symbol=${symbol}&days=100`)
      ]);
      
      const analysisData = await analysisRes.json();
      const historyData = await historyRes.json();
      
      setResult(analysisData);
      setHistory(historyData);
      
      // Start streaming markdown
      const eventSource = new EventSource(`http://localhost:8000/analyze/stream?symbol=${symbol}`);
      eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
          eventSource.close();
        } else {
          setStreamText((prev) => prev + event.data);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
      };
      
    } catch (error) {
      console.error("Analysis failed", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex bg-background text-foreground min-h-screen">
      <Sidebar onAnalyze={handleAnalyze} loading={loading} />
      
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header result={result} />
        
        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
          {!result && !loading && (
             <div className="h-full flex flex-col items-center justify-center text-center space-y-6">
                <div className="w-24 h-24 rounded-3xl bg-blue-600/10 flex items-center justify-center">
                  <Activity className="w-12 h-12 text-blue-500 animate-pulse" />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-bold tracking-tight">Sẵn sàng phân tích</h2>
                  <p className="text-zinc-500 max-w-xs mx-auto text-sm">Nhập mã chứng khoán bên trái để hệ thống AI bắt đầu quét và đánh giá thị trường.</p>
                </div>
             </div>
          )}

          {result && (
            <div className="grid grid-cols-12 gap-8">
              {/* Main Content Area */}
              <div className="col-span-8 space-y-8">
                {/* Visual Chart Placeholder */}
                <div className="glass-panel aspect-video rounded-3xl p-6 flex flex-col border-white/5 shadow-2xl relative overflow-hidden">
                   <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none" />
                   <div className="flex items-center justify-between mb-8">
                      <div className="font-bold flex items-center gap-2"><TrendingUp className="w-4 h-4 text-blue-500" /> Biểu đồ 100 ngày</div>
                      <div className="flex gap-2">
                         <div className="px-3 py-1 rounded-lg bg-white/5 border border-white/5 text-[10px] font-bold">1H</div>
                         <div className="px-3 py-1 rounded-lg bg-blue-600 border border-blue-500 text-[10px] font-bold text-white shadow-lg shadow-blue-900/40">1D</div>
                         <div className="px-3 py-1 rounded-lg bg-white/5 border border-white/5 text-[10px] font-bold">1W</div>
                      </div>
                   </div>
                   <div className="flex-1 flex items-center justify-center border-t border-white/5 mt-auto pt-4 overflow-hidden">
                      <CandlestickChart data={history} />
                   </div>
                </div>

                {/* AI Narrative Section */}
                <div className="glass-panel rounded-3xl p-8 border-white/5 space-y-6">
                  <h3 className="text-lg font-black tracking-tighter uppercase flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-emerald-400" /> Báo Cáo Phân Tích AI
                  </h3>
                  <div className="prose prose-invert max-w-none text-zinc-300 leading-relaxed text-sm">
                    <ReactMarkdown>{streamText || "Đang tạo báo cáo chi tiết..."}</ReactMarkdown>
                  </div>
                </div>
              </div>

              {/* Sidebar Stats Area */}
              <div className="col-span-4 space-y-8">
                 {/* Score Gauge */}
                 <div className="glass-panel rounded-3xl p-6 border-white/5 flex flex-col items-center text-center space-y-4">
                    <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Composite Score</div>
                    <div className="relative w-40 h-40 flex items-center justify-center">
                       <svg className="w-full h-full -rotate-90">
                         <circle cx="80" cy="80" r="70" fill="transparent" stroke="currentColor" strokeWidth="8" className="text-zinc-800" />
                         <circle 
                            cx="80" cy="80" r="70" fill="transparent" stroke="currentColor" strokeWidth="8" 
                            strokeDasharray={440}
                            strokeDashoffset={440 - (440 * result.opinion.confidence)}
                            className="text-blue-500 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)] transition-all duration-1000"
                         />
                       </svg>
                       <div className="absolute flex flex-col items-center">
                          <span className="text-4xl font-black">{(result.opinion.confidence * 100).toFixed(0)}</span>
                          <span className="text-[10px] font-bold text-zinc-500 italic">pts</span>
                       </div>
                    </div>
                    <p className="text-xs font-medium text-zinc-400 leading-snug">
                       Độ tin cậy của thuật toán dựa trên 4 nguồn tín hiệu.
                    </p>
                 </div>

                 {/* Key Levels */}
                 <div className="glass-panel rounded-3xl p-6 border-white/5 space-y-4">
                    <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                       <TrendingUp className="w-3 h-3" /> Ngưỡng Kỹ Thuật
                    </div>
                    <div className="space-y-3">
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-zinc-400">Kháng cự 1</span>
                          <span className="text-sm font-black text-red-500">{result.opinion.key_levels?.resistance_1?.toLocaleString() || "---"}</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-zinc-400">Kháng cự 2</span>
                          <span className="text-sm font-bold text-red-400/80 italic">{result.opinion.key_levels?.resistance_2?.toLocaleString() || "---"}</span>
                       </div>
                       <div className="h-px bg-white/5 my-2" />
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-zinc-400">Hỗ trợ 1</span>
                          <span className="text-sm font-black text-emerald-500">{result.opinion.key_levels?.support_1?.toLocaleString() || "---"}</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-zinc-400">Hỗ trợ 2</span>
                          <span className="text-sm font-bold text-emerald-400/80 italic">{result.opinion.key_levels?.support_2?.toLocaleString() || "---"}</span>
                       </div>
                    </div>
                 </div>

                 {/* Key Points */}
                 <div className="space-y-3">
                    <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest px-2">Điểm nhấn đầu tư</div>
                    {result.opinion.key_points.map((point, idx) => (
                       <motion.div 
                          key={idx} 
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="glass-panel rounded-2xl p-4 border-white/5 text-xs font-medium flex gap-3 leading-relaxed"
                       >
                          <div className="w-5 h-5 rounded-full bg-blue-600/20 flex items-center justify-center shrink-0">
                            <CheckCircle2 className="w-3 h-3 text-blue-500" />
                          </div>
                          {point}
                       </motion.div>
                    ))}
                 </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
