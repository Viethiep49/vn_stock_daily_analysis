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
  BarChart2,
  PieChart,
  RefreshCw,
  Info
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
      const historyData = await fetchHistory(cleanSymbol);
      setHistory(historyData);

      const result = await runAnalysis(cleanSymbol);
      setData(result);

      setIsStreaming(true);
      streamAnalysis(
        cleanSymbol,
        (text) => setStreamingText(text),
        () => setIsStreaming(false)
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Đã có lỗi xảy ra khi kết nối API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      await handleSearch();
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isPositive = data ? data.quote.percent_change >= 0 : true;

  return (
    <div className="space-y-6 animate-fade-up max-w-[1400px] mx-auto pb-12">
      {/* Search Header */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-surface-2/50 p-4 rounded-2xl border border-white/5 backdrop-blur-md">
        <div className="flex-1 w-full max-w-xl">
          <form onSubmit={handleSearch} className="relative group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 group-focus-within:text-primary transition-colors">
              <Search size={18} />
            </div>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="Nhập mã chứng khoán (vd: VNM, FPT...)"
              className="w-full bg-black/40 border border-white/10 rounded-xl pl-12 pr-32 py-3.5 text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all font-mono text-sm uppercase"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 bg-primary/20 hover:bg-primary/30 text-primary px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Zap size={14} />}
              {loading ? "ĐANG TẢI" : "PHÂN TÍCH"}
            </button>
          </form>
        </div>
        
        {data && (
          <div className="flex items-center gap-3 text-sm">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white/70">
              <Shield size={14} className="text-secondary-light" />
              <span>Multi-Agent:</span>
              <span className="font-bold text-white">{data.is_multi_agent ? "ON" : "OFF"}</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-sm flex items-center gap-3 shadow-lg">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Content - Left Column (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Header & Chart Card */}
            <div className="glass-card overflow-hidden">
              <div className="p-6 border-b border-white/5 bg-gradient-to-b from-white/[0.02] to-transparent">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                        {data.info.symbol}
                      </h1>
                      <span className="px-2.5 py-1 bg-white/10 rounded text-xs font-medium text-white/80">
                        {data.info.exchange}
                      </span>
                    </div>
                    <p className="text-white/60 text-sm flex items-center gap-2">
                      {data.info.company_name}
                      <span className="w-1 h-1 rounded-full bg-white/20" />
                      {data.info.industry}
                    </p>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-3xl md:text-4xl font-bold font-mono tracking-tight">
                      {data.quote.last_price.toLocaleString()}
                    </div>
                    <div className={`flex items-center justify-end gap-1 font-mono text-sm font-semibold mt-1 ${isPositive ? 'text-success' : 'text-danger'}`}>
                      {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                      {isPositive ? '+' : ''}{data.quote.change.toLocaleString()} ({isPositive ? '+' : ''}{data.quote.percent_change.toFixed(2)}%)
                    </div>
                  </div>
                </div>
              </div>

              {/* Chart */}
              <div className="h-[300px] w-full p-4 -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={isPositive ? '#10B981' : '#EF4444'} stopOpacity={0.2}/>
                        <stop offset="95%" stopColor={isPositive ? '#10B981' : '#EF4444'} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      hide 
                    />
                    <YAxis 
                      domain={['auto', 'auto']} 
                      orientation="right"
                      tick={{fill: 'rgba(255,255,255,0.3)', fontSize: 11, fontFamily: 'monospace'}}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => val.toLocaleString()}
                      width={60}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                      itemStyle={{ color: '#fff', fontWeight: 600 }}
                      labelStyle={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', marginBottom: '4px' }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="close" 
                      stroke={isPositive ? '#10B981' : '#EF4444'} 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorPrice)" 
                      animationDuration={1000}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-card p-4">
                <div className="flex items-center gap-2 text-xs text-white/40 uppercase mb-2 font-semibold">
                  <Activity size={14} /> Khối Lượng
                </div>
                <div className="text-xl font-mono font-medium">
                  {data.quote.volume.toLocaleString()}
                </div>
              </div>
              <div className="glass-card p-4">
                <div className="flex items-center gap-2 text-xs text-white/40 uppercase mb-2 font-semibold">
                  <PieChart size={14} /> Mở / Cao / Thấp
                </div>
                <div className="text-sm font-mono text-white/80 space-y-1">
                  <div className="flex justify-between"><span>O:</span><span>{data.quote.open?.toLocaleString() || '-'}</span></div>
                  <div className="flex justify-between text-success"><span>H:</span><span>{data.quote.high?.toLocaleString() || '-'}</span></div>
                  <div className="flex justify-between text-danger"><span>L:</span><span>{data.quote.low?.toLocaleString() || '-'}</span></div>
                </div>
              </div>
              <div className="glass-card p-4 bg-success/5 border-success/10">
                <div className="flex items-center gap-2 text-xs text-success/70 uppercase mb-2 font-semibold">
                  <TrendingUp size={14} /> Kháng Cự
                </div>
                <div className="text-sm font-mono space-y-1">
                  <div className="flex justify-between"><span>R1:</span><span className="font-medium text-success">{data.opinion.key_levels.resistance_1?.toLocaleString() || '-'}</span></div>
                  <div className="flex justify-between"><span>R2:</span><span className="font-medium text-success">{data.opinion.key_levels.resistance_2?.toLocaleString() || '-'}</span></div>
                </div>
              </div>
              <div className="glass-card p-4 bg-danger/5 border-danger/10">
                <div className="flex items-center gap-2 text-xs text-danger/70 uppercase mb-2 font-semibold">
                  <TrendingDown size={14} /> Hỗ Trợ
                </div>
                <div className="text-sm font-mono space-y-1">
                  <div className="flex justify-between"><span>S1:</span><span className="font-medium text-danger">{data.opinion.key_levels.support_1?.toLocaleString() || '-'}</span></div>
                  <div className="flex justify-between"><span>S2:</span><span className="font-medium text-danger">{data.opinion.key_levels.support_2?.toLocaleString() || '-'}</span></div>
                </div>
              </div>
            </div>

            {/* Technical Summary */}
            <div className="glass-card p-6">
              <div className="flex items-center gap-2 mb-4 text-white/80">
                <BarChart2 size={18} className="text-secondary" />
                <h3 className="font-bold">Phân Tích Kỹ Thuật</h3>
              </div>
              <div className="prose prose-invert prose-sm max-w-none text-white/70 leading-relaxed">
                <ReactMarkdown>{data.tech_summary || "Không có dữ liệu phân tích kỹ thuật."}</ReactMarkdown>
              </div>
            </div>

          </div>

          {/* AI Analysis - Right Column (1/3) */}
          <div className="space-y-6">
            
            {/* AI Signal Card */}
            <div className="glass-card p-6 relative overflow-hidden">
              <div className="absolute -right-12 -top-12 w-32 h-32 bg-primary/10 rounded-full blur-2xl pointer-events-none" />
              
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2 text-white/80">
                  <Target size={18} className="text-primary" />
                  <h3 className="font-bold">Tín Hiệu AI</h3>
                </div>
                <div className={`px-3 py-1 rounded-md text-xs font-bold tracking-wider ${
                  data.opinion.signal === 'BUY' ? 'bg-success/20 text-success border border-success/30' : 
                  data.opinion.signal === 'SELL' ? 'bg-danger/20 text-danger border border-danger/30' : 
                  'bg-warning/20 text-warning border border-warning/30'
                }`}>
                  {data.opinion.signal}
                </div>
              </div>

              <div className="mb-6">
                <div className="flex justify-between text-xs text-white/60 mb-2">
                  <span>Độ tin cậy (Confidence)</span>
                  <span className="font-mono">{((data.opinion.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-primary to-primary-light transition-all duration-1000" 
                    style={{ width: `${(data.opinion.confidence || 0) * 100}%` }}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-semibold text-white/40 uppercase">Luận Điểm Chính</h4>
                {data.opinion.key_points.map((point, i) => (
                  <div key={i} className="flex gap-2.5 text-sm text-white/70">
                    <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-white/20 shrink-0" />
                    <p className="leading-snug">{point}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Agent Terminal */}
            <div className="glass-card flex flex-col h-[400px]">
              <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between bg-black/20 rounded-t-xl">
                <div className="flex items-center gap-2 text-xs font-medium text-white/60">
                  <Zap size={14} className={isStreaming ? "text-primary animate-pulse" : "text-white/40"} />
                  Agent Report
                </div>
                {isStreaming && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                  </span>
                )}
              </div>
              
              <div className="flex-1 p-4 overflow-y-auto custom-scrollbar font-sans text-sm text-white/80">
                <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-headings:text-primary-light prose-a:text-secondary-light">
                  <ReactMarkdown>
                    {streamingText || (loading ? "*Đang khởi tạo AI Agent...*" : data.llm_analysis || "*Chưa có báo cáo AI.*")}
                  </ReactMarkdown>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Empty State / Welcome */}
      {!data && !loading && !error && (
        <div className="text-center py-20 animate-fade-in">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 text-white/20 mb-6">
            <Info size={32} />
          </div>
          <h2 className="text-2xl font-bold mb-2">Sẵn sàng phân tích</h2>
          <p className="text-white/40 max-w-md mx-auto">
            Nhập mã cổ phiếu vào ô tìm kiếm phía trên để nhận báo cáo phân tích toàn diện từ AI Agent.
          </p>
        </div>
      )}
    </div>
  );
}
