import Navbar from "@/components/Navbar";
import StockDashboard from "@/components/StockDashboard";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-black">
      <Navbar />
      <div className="pt-24 pb-12">
        <div className="section-container">
          <div className="mb-12 text-center space-y-4">
            <h1 className="font-display text-4xl lg:text-6xl font-bold">
              <span className="gradient-text-white">VN Stock</span>
              <br />
              <span className="gradient-text-gold">Personal Analyzer</span>
            </h1>
            <p className="text-white/50 text-lg max-w-xl mx-auto">
              Hệ thống phân tích cổ phiếu cá nhân. Nhập mã chứng khoán để bắt đầu.
            </p>
          </div>
          
          <StockDashboard />
        </div>
      </div>
      <Footer />
    </main>
  );
}
