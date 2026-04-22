"use client";

const LINKS = {
  product: ["Tính Năng", "Bảo Mật", "Tích Hợp"],
  resources: ["Tài Liệu", "API Reference", "Chiến Lược", "Testing Guide"],
  legal: ["MIT License", "Privacy Policy", "Điều Khoản"],
};

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-16" role="contentinfo">
      <div className="section-container">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg gradient-gold flex items-center justify-center glow-gold">
                <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5" aria-hidden="true">
                  <path d="M3 17L9 11L13 15L21 7" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M17 7H21V11" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <span className="font-display font-bold text-base">
                <span className="gradient-text-gold">VN</span>
                <span className="text-white"> Stock AI</span>
              </span>
            </div>
            <p className="text-sm text-white/40 leading-relaxed max-w-xs">
              Hệ thống phân tích cổ phiếu Việt Nam bằng AI. Mã nguồn mở, bảo mật, và mạnh mẽ.
            </p>
            <div className="flex items-center gap-3">
              {/* GitHub */}
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                id="footer-github"
                className="w-8 h-8 rounded-lg glass-card flex items-center justify-center text-white/40 hover:text-white transition-colors cursor-pointer"
                aria-label="GitHub Repository"
              >
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4" aria-hidden="true">
                  <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
                </svg>
              </a>
            </div>
          </div>

          {/* Product links */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4 font-display">Sản Phẩm</h3>
            <ul className="space-y-3 list-none" role="list">
              {LINKS.product.map((l) => (
                <li key={l}>
                  <a href="#" className="text-sm text-white/40 hover:text-white transition-colors cursor-pointer">
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4 font-display">Tài Nguyên</h3>
            <ul className="space-y-3 list-none" role="list">
              {LINKS.resources.map((l) => (
                <li key={l}>
                  <a href="#" className="text-sm text-white/40 hover:text-white transition-colors cursor-pointer">
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Stack badges */}
          <div>
            <h3 className="text-sm font-semibold text-white mb-4 font-display">Tech Stack</h3>
            <div className="flex flex-wrap gap-2">
              {[
                { label: "Python 3.11", color: "#3B82F6" },
                { label: "Next.js 16", color: "#F8FAFC" },
                { label: "FastAPI", color: "#10B981" },
                { label: "LiteLLM", color: "#F59E0B" },
                { label: "vnstock", color: "#EF4444" },
                { label: "TailwindCSS", color: "#38BDF8" },
              ].map((t) => (
                <span
                  key={t.label}
                  className="text-xs px-2.5 py-1 rounded-full font-mono"
                  style={{ background: `${t.color}12`, color: t.color, border: `1px solid ${t.color}25` }}
                >
                  {t.label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-white/25">
            © 2025 VN Stock AI. MIT License. Không phải tư vấn tài chính.
          </p>
          <div className="flex items-center gap-4">
            {LINKS.legal.map((l) => (
              <a key={l} href="#" className="text-xs text-white/25 hover:text-white/60 transition-colors cursor-pointer">
                {l}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-dot" aria-hidden="true" />
            <span className="text-xs text-emerald-400 font-mono">Hệ Thống Hoạt Động</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
