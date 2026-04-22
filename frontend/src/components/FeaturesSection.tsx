"use client";

const FEATURES = [
  {
    id: "realtime-data",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Dữ Liệu Thời Gian Thực",
    description: "Feed trực tiếp từ HOSE & HNX qua vnstock v3.5+. Giá, khối lượng và dữ liệu kỹ thuật cập nhật từng giây.",
    color: "#F59E0B",
    stats: "< 1s latency",
  },
  {
    id: "multi-agent",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.93 4.93l2.12 2.12M16.95 16.95l2.12 2.12M4.93 19.07l2.12-2.12M16.95 7.05l2.12-2.12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "Multi-Agent AI",
    description: "Nhiều AI agents phân tích song song: Technical Analyst, Fundamental Scout, Risk Manager và Decision Agent tổng hợp.",
    color: "#3B82F6",
    stats: "5 agents",
  },
  {
    id: "vsa-canslim",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path d="M3 3v18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 16l4-4 4 4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Chiến Lược VSA & CANSLIM",
    description: "Áp dụng chiến lược trading chuyên sâu: Volume Spread Analysis, CANSLIM và các strategy tùy chỉnh YAML.",
    color: "#10B981",
    stats: "10+ strategies",
  },
  {
    id: "smart-alerts",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Cảnh Báo Thông Minh",
    description: "Tín hiệu Buy/Sell/Hold tự động gửi qua Telegram và Discord với phân tích chi tiết từ AI.",
    color: "#10B981",
    stats: "Telegram + Discord",
  },
  {
    id: "circuit-breaker",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Circuit Breaker & Trần/Sàn",
    description: "Phát hiện tự động cổ phiếu chạm trần/sàn, thanh khoản bất thường và cảnh báo rủi ro ngay lập tức.",
    color: "#EF4444",
    stats: "VN market rules",
  },
  {
    id: "backtest",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5" aria-hidden="true">
        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    title: "Backtesting",
    description: "Kiểm tra chiến lược trên dữ liệu lịch sử với báo cáo hiệu suất chi tiết: Sharpe ratio, max drawdown và win rate.",
    color: "#F59E0B",
    stats: "5 năm data",
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-28" aria-label="Features">
      <div className="section-container">
        {/* Section header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card border border-blue-500/20 text-sm mb-4">
            <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-blue-400" aria-hidden="true">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-blue-400 font-medium">Công Nghệ</span>
          </div>
          <h2 className="font-display text-4xl lg:text-5xl font-bold gradient-text-white">
            Mọi Thứ Bạn Cần
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            Bộ công cụ phân tích chuyên sâu dành cho nhà đầu tư cá nhân và chuyên nghiệp
          </p>
        </div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5" role="list">
          {FEATURES.map((feature, i) => (
            <div
              key={feature.id}
              id={`feature-card-${feature.id}`}
              className="glass-card p-6 space-y-4 group cursor-pointer"
              style={{ animationDelay: `${i * 0.1}s` }}
              role="listitem"
            >
              {/* Icon */}
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 group-hover:scale-110"
                style={{ background: `${feature.color}18`, color: feature.color }}
              >
                {feature.icon}
              </div>

              {/* Content */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-display font-semibold text-base text-white">
                    {feature.title}
                  </h3>
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded-full"
                    style={{ background: `${feature.color}15`, color: feature.color }}
                  >
                    {feature.stats}
                  </span>
                </div>
                <p className="text-sm text-white/50 leading-relaxed">
                  {feature.description}
                </p>
              </div>

              {/* Bottom accent line */}
              <div
                className="h-px w-0 group-hover:w-full transition-all duration-300 rounded-full"
                style={{ background: `linear-gradient(90deg, ${feature.color}, transparent)` }}
                aria-hidden="true"
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
