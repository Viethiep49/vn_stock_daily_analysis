import type { Metadata } from "next";
import { Inter, Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "VN Stock AI — Phân Tích Cổ Phiếu Thông Minh",
  description:
    "Hệ thống phân tích cổ phiếu Việt Nam bằng AI. Real-time data từ HOSE/HNX, multi-agent analysis, và cảnh báo thông minh qua Telegram & Discord.",
  keywords: "cổ phiếu Việt Nam, phân tích AI, HOSE, HNX, vnstock, fintech",
  openGraph: {
    title: "VN Stock AI — Phân Tích Cổ Phiếu Thông Minh",
    description: "AI-powered Vietnamese stock market analysis",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="vi"
      className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-black text-white">
        {children}
      </body>
    </html>
  );
}
