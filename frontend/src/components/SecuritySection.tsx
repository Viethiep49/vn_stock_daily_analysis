"use client";

const SECURITY_FEATURES = [
  {
    id: "api-key-vault",
    title: "API Key Vault",
    description: "Tất cả API key được lưu trong .env file cục bộ, không bao giờ được gửi lên cloud. Zero-trust architecture.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" aria-hidden="true">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" strokeWidth="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    badge: "Zero-Trust",
    badgeColor: "#F59E0B",
  },
  {
    id: "read-only-api",
    title: "Read-Only API Access",
    description: "Hệ thống chỉ đọc dữ liệu thị trường. Không có quyền giao dịch trực tiếp — tài sản của bạn luôn an toàn.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" aria-hidden="true">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
      </svg>
    ),
    badge: "No Trade Access",
    badgeColor: "#10B981",
  },
  {
    id: "local-first",
    title: "Local-First Processing",
    description: "Toàn bộ phân tích chạy trên máy của bạn. Dữ liệu cổ phiếu không bao giờ rời khỏi thiết bị.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" aria-hidden="true">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" strokeWidth="2" />
        <line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    badge: "On-Premise",
    badgeColor: "#3B82F6",
  },
  {
    id: "encrypted-comms",
    title: "Encrypted Communications",
    description: "Thông báo Telegram và Discord được mã hóa TLS. Bot token bảo mật, không lưu lịch sử chat.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6" aria-hidden="true">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    badge: "TLS/E2E",
    badgeColor: "#8B5CF6",
  },
];

const TRUST_INDICATORS = [
  { id: "opensource", label: "Open Source", desc: "MIT License", icon: "🔓" },
  { id: "nodata", label: "Không Thu Thập Data", desc: "Privacy First", icon: "🛡️" },
  { id: "github", label: "GitHub Verified", desc: "Audited Code", icon: "✓" },
  { id: "vnstock", label: "vnstock Official", desc: "Nguồn Dữ Liệu", icon: "📊" },
];

export default function SecuritySection() {
  return (
    <section id="security" className="py-28 relative overflow-hidden" aria-label="Security Features">
      {/* Background gradient */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 50%, rgba(59,130,246,0.05) 0%, transparent 70%)",
        }}
        aria-hidden="true"
      />

      <div className="section-container relative z-10">
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card border border-emerald-500/20 text-sm mb-4">
            <svg viewBox="0 0 24 24" fill="none" className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span className="text-emerald-400 font-medium">Bảo Mật</span>
          </div>
          <h2 className="font-display text-4xl lg:text-5xl font-bold gradient-text-white">
            Bảo Mật Tuyệt Đối
          </h2>
          <p className="text-white/50 text-lg max-w-xl mx-auto">
            Kiến trúc local-first. Tài sản và dữ liệu của bạn luôn nằm trong tầm kiểm soát của bạn.
          </p>
        </div>

        {/* Main layout: shield graphic + cards */}
        <div className="grid lg:grid-cols-2 gap-12 items-center mb-16">
          {/* Shield Graphic */}
          <div className="relative flex items-center justify-center">
            <div
              className="w-64 h-64 rounded-full"
              style={{
                background: "radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%)",
                boxShadow: "0 0 80px rgba(16,185,129,0.1)",
              }}
              aria-hidden="true"
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="glass-card p-10 rounded-full" style={{ border: "1px solid rgba(16,185,129,0.2)" }}>
                <svg viewBox="0 0 24 24" fill="none" className="w-24 h-24 text-emerald-400" aria-hidden="true">
                  <path
                    d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="rgba(16,185,129,0.06)"
                  />
                  <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            </div>

            {/* Orbiting badges */}
            {[0, 90, 180, 270].map((deg, i) => {
              const rad = (deg * Math.PI) / 180;
              const x = 50 + 42 * Math.cos(rad);
              const y = 50 + 42 * Math.sin(rad);
              const labels = ["SSL", "E2E", "Zero-Trust", "Local"];
              const colors = ["#F59E0B", "#10B981", "#3B82F6", "#8B5CF6"];
              return (
                <div
                  key={deg}
                  className="absolute w-16 h-16 flex items-center justify-center"
                  style={{
                    left: `${x}%`,
                    top: `${y}%`,
                    transform: "translate(-50%, -50%)",
                  }}
                  aria-hidden="true"
                >
                  <div
                    className="glass-card px-2 py-1 text-center"
                    style={{ border: `1px solid ${colors[i]}30` }}
                  >
                    <span className="text-xs font-mono font-bold" style={{ color: colors[i] }}>
                      {labels[i]}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Security Cards */}
          <div className="grid sm:grid-cols-2 gap-4" role="list">
            {SECURITY_FEATURES.map((feat) => (
              <div
                key={feat.id}
                id={`security-${feat.id}`}
                className="glass-card p-5 space-y-3 group cursor-pointer"
                role="listitem"
              >
                <div className="flex items-start justify-between">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 group-hover:scale-110"
                    style={{ background: `${feat.badgeColor}15`, color: feat.badgeColor }}
                  >
                    {feat.icon}
                  </div>
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded-full font-semibold"
                    style={{ background: `${feat.badgeColor}15`, color: feat.badgeColor }}
                  >
                    {feat.badge}
                  </span>
                </div>
                <h3 className="font-display font-semibold text-sm text-white">{feat.title}</h3>
                <p className="text-xs text-white/45 leading-relaxed">{feat.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Indicators bar */}
        <div
          className="glass-card p-6"
          style={{ border: "1px solid rgba(255,255,255,0.06)" }}
          role="region"
          aria-label="Trust indicators"
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <p className="text-sm text-white/40 font-medium">Đảm Bảo & Chứng Nhận</p>
            <div className="flex flex-wrap items-center gap-6 sm:gap-10">
              {TRUST_INDICATORS.map((ti) => (
                <div key={ti.id} id={`trust-${ti.id}`} className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-sm">
                    {ti.icon}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white">{ti.label}</div>
                    <div className="text-xs text-white/35">{ti.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
