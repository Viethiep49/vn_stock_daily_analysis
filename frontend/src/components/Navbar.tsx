"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`fixed top-4 left-4 right-4 z-50 rounded-xl transition-all duration-300 ${
        scrolled ? "glass-nav shadow-2xl" : "bg-transparent"
      }`}
      role="banner"
    >
      <nav
        className="section-container flex items-center justify-between h-16"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2.5 cursor-pointer"
          aria-label="VN Stock AI Homepage"
        >
          <div className="w-8 h-8 rounded-lg gradient-gold flex items-center justify-center glow-gold">
            <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5" aria-hidden="true">
              <path
                d="M3 17L9 11L13 15L21 7"
                stroke="#000"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M17 7H21V11" stroke="#000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="font-display font-bold text-lg tracking-tight">
            <span className="gradient-text-gold">VN</span>
            <span className="text-white"> Stock Personal</span>
          </span>
        </Link>

        {/* Status Indicator */}
        <div className="flex items-center gap-3">
           <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-card border border-emerald-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] text-emerald-400 font-mono font-bold uppercase tracking-wider">System Live</span>
           </div>
        </div>
      </nav>
    </header>
  );
}
