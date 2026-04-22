"use client";

import React from "react";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface HistoryData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isUp = data.close >= data.open;
    return (
      <div className="glass-panel p-3 rounded-xl border-white/10 shadow-2xl text-[11px] space-y-1">
        <p className="font-bold text-zinc-400 mb-2">{data.date}</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
           <span className="text-zinc-500">Mở:</span> <span className="font-medium text-white">{data.open.toLocaleString()}</span>
           <span className="text-zinc-500">Cao:</span> <span className="font-medium text-white">{data.high.toLocaleString()}</span>
           <span className="text-zinc-500">Thấp:</span> <span className="font-medium text-white">{data.low.toLocaleString()}</span>
           <span className="text-zinc-500">Đóng:</span> <span className={isUp ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>{data.close.toLocaleString()}</span>
           <span className="text-zinc-500">Khối lượng:</span> <span className="font-medium text-white">{data.volume.toLocaleString()}</span>
        </div>
      </div>
    );
  }
  return null;
};

export const CandlestickChart = ({ data }: { data: HistoryData[] }) => {
  if (!data || data.length === 0) return null;

  // Prepare data for Recharts (OHLC as a single range for Bar)
  const chartData = data.map((d) => ({
    ...d,
    // Bar height will be |close - open|
    // Bar start will be min(open, close)
    candle: [d.open, d.close],
    lowHigh: [d.low, d.high]
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ffffff05" />
        <XAxis 
          dataKey="date" 
          axisLine={false} 
          tickLine={false} 
          tick={{ fontSize: 9, fill: "#666" }}
          minTickGap={50}
        />
        <YAxis 
          domain={["auto", "auto"]} 
          orientation="right" 
          axisLine={false} 
          tickLine={false} 
          tick={{ fontSize: 9, fill: "#666" }} 
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        
        {/* Volume Bar */}
        <Bar dataKey="volume" yAxisId={0} fillOpacity={0.1} radius={[2, 2, 0, 0]}>
           {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.close >= entry.open ? "#10b981" : "#ef4444"} />
           ))}
        </Bar>

        {/* This is a simplified candlestick using a custom Bar implementation */}
        {/* For a more precise one, we'd use a custom shape, but this is a good premium approximation */}
        <Bar dataKey="candle" radius={[2, 2, 2, 2]}>
          {chartData.map((entry, index) => (
             <Cell key={`cell-${index}`} fill={entry.close >= entry.open ? "#10b981" : "#ef4444"} />
          ))}
        </Bar>
      </ComposedChart>
    </ResponsiveContainer>
  );
};
