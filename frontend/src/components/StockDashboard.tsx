"use client";

import { useState, useEffect } from "react";
import { runAnalysis, fetchHistory, streamAnalysis, AnalysisResult, HistoryItem } from "@/lib/api";
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Shield, 
  Zap, 
  Target, 
  AlertCircle,
  ChevronRight,
  RefreshCw
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts";
import ReactMarkdown from "react-markdown";

export default function StockDashboard() {
  const [symbol, setSymbol] = useState("VNM");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanSymbol = symbol.trim().toUpperCase().split('.')[0];
    if (!cleanSymbol) return;

    setLoading(true);
    setError(null);
    setStreamingText("");
    
    try {
      // 1. Fetch History first for immediate visual feedback
      const historyData = await fetchHistory(cleanSymbol);
      setHistory(historyData);

      // 2. Run Analysis
      const result = await runAnalysis(cleanSymbol);
      setData(result);

      // 3. Start Streaming Analysis
      setIsStreaming(true);
      streamAnalysis(
        cleanSymbol,
        (text) => setStreamingText(text),
        () => setIsStreaming(false)
      );
    } catch (err: any) {
      setError(err.message || "Đã có lỗi xảy ra khi kết nối API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Search Bar - Premium Floating Design */}
      <div className="glass-card p-2 flex items-center shadow-2xl">
        <form onSubmit={handleSearch} className="relative flex-1 group">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-amber-500 transition-colors">
            <Search size={20} />
          </div>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="Nhập mã chứng khoán (vd: VNM, FPT, HPG...)"
            className="w-full bg-transparent border-none rounded-xl pl-12 pr-4 py-4 text-white focus:outline-none transition-all font-display text-lg"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary py-2 px-6 rounded-lg text-sm font-bold flex items-center gap-2"
          >
            {loading ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
            {loading ? "ĐANG PHÂN TÍCH" : "PHÂN TÍCH AI"}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-center gap-3">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      <div className="grid lg:grid-cols-12 gap-6">
        {/* Main Dashboard Area */}
        <div className="lg:col-span-8 space-y-6">
          {/* Price Summary Card */}
          <div className="glass-card p-6 overflow-hidden relative">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 blur-[100px] -mr-32 -mt-32" />
            
            <div className="flex justify-between items-end mb-8 relative z-10">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-3xl font-bold font-display tracking-tight">
                    {data?.info.company_name || symbol}
                  </h2>
                  <span className="px-2 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] font-mono text-white/40">
                    {data?.info.exchange || "HOSE"}
                  </span>
                </div>
                <p className="text-white/40 font-mono text-sm uppercase tracking-wider">
                  {data?.info.industry || "Stock Market"}
                </p>
              </div>
              
              <div className="text-right">
                <div className="text-4xl font-bold font-mono tracking-tighter">
                  {data?.quote.last_price.toLocaleString()}
                  <span className="text-lg text-white/30 ml-1">đ</span>
                </div>
                <div className={`flex items-center justify-end gap-1 font-mono text-sm font-bold ${data && data.quote.percent_change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {data && data.quote.percent_change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {data && data.quote.percent_change >= 0 ? '+' : ''}{data?.quote.percent_change.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Recharts Component */}
            <div className="h-[350px] w-full mt-4 -mx-6 px-2">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    hide 
                  />
                  <YAxis 
                    domain={['auto', 'auto']} 
                    orientation="right"
                    tick={{fill: 'rgba(255,255,255,0.2)', fontSize: 10}}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(val) => val.toLocaleString()}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ color: '#F59E0B' }}
                    labelStyle={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="close" 
                    stroke="#F59E0B" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorPrice)" 
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Kháng Cự 1", value: data?.opinion.key_levels.resistance_1, color: "text-red-400", icon: <TrendingUp size={12} /> },
              { label: "Hỗ Trợ 1", value: data?.opinion.key_levels.support_1, color: "text-emerald-400", icon: <TrendingDown size={12} /> },
              { label: "Khối Lượng", value: data?.quote.volume.toLocaleString(), color: "text-white", icon: <Activity size={12} /> },
              { label: "Tín Hiệu", value: data?.opinion.signal || "HOLD", color: data?.opinion.signal === 'BUY' ? 'text-emerald-400' : data?.opinion.signal === 'SELL' ? 'text-red-400' : 'text-amber-400', icon: <Target size={12} /> }
            ].map((metric, i) => (
              <div key={i} className="glass-card p-4 group hover:border-white/20 transition-all">
                <div className="flex items-center gap-2 text-[10px] font-bold text-white/30 uppercase tracking-widest mb-1">
                  {metric.icon}
                  {metric.label}
                </div>
                <div className={`text-xl font-mono font-bold ${metric.color}`}>
                  {typeof metric.value === 'number' ? metric.value.toLocaleString() : (metric.value || "---")}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Analysis Side Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-card h-full flex flex-col min-h-[500px]">
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Zap size={18} className="text-amber-500" />
                  {isStreaming && <div className="absolute inset-0 text-amber-500 animate-ping"><Zap size={18} /></div>}
                </div>
                <h3 className="font-display font-bold">Báo Cáo AI Agent</h3>
              </div>
              {isStreaming && (
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-amber-500/10 border border-amber-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-[10px] font-mono text-amber-500 font-bold uppercase">Streaming</span>
                </div>
              )}
            </div>

            <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
              <div className="prose prose-invert prose-sm max-w-none prose-headings:font-display prose-headings:text-amber-500 prose-p:text-white/70 prose-p:leading-relaxed prose-strong:text-white">
                <ReactMarkdown>
                  {streamingText || (loading ? "Đang thu thập dữ liệu thị trường và kích hoạt Agent..." : "Hệ thống sẵn sàng. Nhập mã cổ phiếu và nhấn Phân Tích để nhận báo cáo từ AI.")}
                </ReactMarkdown>
              </div>

              {data && !isStreaming && (
                <div className="mt-8 pt-8 border-t border-white/5 animate-fade-in">
                  <div className="flex items-center gap-2 mb-4">
                    <Shield size={14} className="text-emerald-500" />
                    <h4 className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em]">Tóm Tắt Tín Hiệu</h4>
                  </div>
                  <div className="space-y-3">
                    {data.opinion.key_points.map((point, i) => (
                      <div key={i} className="flex gap-3 text-sm text-white/60 group">
                        <div className="mt-1.5 w-1 h-1 rounded-full bg-amber-500 group-hover:scale-150 transition-transform" />
                        <p>{point}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Insight */}
            <div className="p-4 bg-white/[0.02] border-t border-white/5">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-white/20">Confidence Score</span>
                <span className="text-amber-500">{((data?.opinion.confidence || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-1.5 w-full h-1 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-amber-500 transition-all duration-1000" 
                  style={{ width: `${(data?.opinion.confidence || 0) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
