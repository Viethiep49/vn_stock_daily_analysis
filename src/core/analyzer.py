import logging
from typing import Dict, Any
from datetime import datetime
from src.data_provider.vnstock_provider import VNStockProvider
from src.data_provider.fallback_router import FallbackRouter
from src.utils.validator import VNStockValidator
from src.market.circuit_breaker import CircuitBreakerHandler
from src.core.llm_client import LiteLLMClient

logger = logging.getLogger(__name__)


class Analyzer:
    """Core orchestrator cho phân tích một cổ phiếu cụ thể"""

    def __init__(self):
        # Setup data providers
        vnstock = VNStockProvider()
        # fallback can have more providers
        self.router = FallbackRouter([vnstock])

        # Setup tools
        self.circuit_breaker = CircuitBreakerHandler()
        self.llm = LiteLLMClient()

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Quy trình phân tích chính"""
        logger.info(f"Bắt đầu phân tích cho mã {symbol}")

        # 1. Validate
        is_valid, msg = VNStockValidator.validate(symbol)
        if not is_valid:
            return {"symbol": symbol, "error": msg, "status": "failed"}

        normalized_symbol = VNStockValidator.normalize(symbol)

        # 2. Fetch data
        try:
            info = self.router.execute_with_fallback(
                "get_stock_info", normalized_symbol)
            quote = self.router.execute_with_fallback(
                "get_realtime_quote", normalized_symbol)

            # Lấy 3 tháng gần nhất để tính indicators
            three_months_ago = (datetime.today(
            ) - __import__('datetime').timedelta(days=90)).strftime('%Y-%m-%d')
            df = self.router.execute_with_fallback(
                "get_historical_data",
                normalized_symbol,
                three_months_ago,
                datetime.today().strftime('%Y-%m-%d'))

            # 3. Circuit breaker — dùng giá đóng cửa hôm qua làm tham chiếu
            cb_status = None
            if not df.empty and len(df) >= 2 and 'close' in df.columns:
                prev_close = float(df.iloc[-2]['close'])
                current_price = quote.get('price', 0)
                if prev_close > 0 and current_price > 0:
                    self.circuit_breaker.set_reference_price(
                        normalized_symbol, prev_close)
                    cb_status = self.circuit_breaker.check_limit_status(
                        normalized_symbol, current_price)

            # 4. Tính thêm chỉ số kỹ thuật đơn giản từ lịch sử
            tech_summary = ""
            if not df.empty and len(df) >= 20 and 'close' in df.columns:
                closes = df['close'].astype(float)
                ma5 = closes.tail(5).mean()
                ma20 = closes.tail(20).mean()
                avg_vol = df['volume'].tail(
                    20).mean() if 'volume' in df.columns else 0
                latest_vol = quote.get('volume', 0)
                vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1

                tech_summary = (
                    f"MA5={ma5*1000:,.0f}đ | MA20={ma20*1000:,.0f}đ | "
                    f"KL hôm nay/TB20: {vol_ratio:.1f}x"
                )

            # 5. Build LLM context chi tiết
            context = f"""
Mã chứng khoán: {normalized_symbol}
Công ty: {info.get('company_name', normalized_symbol)}
Ngành: {info.get('industry', 'N/A')} | Sàn: {info.get('exchange', 'HOSE')}
Website: {info.get('website', '')}

Giá đóng cửa gần nhất: {quote.get('price'):,.0f}đ
Thay đổi: {quote.get('change', 0):+.0f}đ ({quote.get('change_pct', 0):+.2f}%)
OHLC: Mở {quote.get('open', 0):,.0f} | Cao {quote.get('high', 0):,.0f} | Thấp {quote.get('low', 0):,.0f}
Khối lượng: {quote.get('volume', 0):,.0f} cổ phiếu

Chỉ số kỹ thuật (từ {len(df)} phiên): {tech_summary}
Cảnh báo rủi ro: {cb_status.get('warning') if cb_status else 'Không có cảnh báo trần/sàn'}
"""

            prompt = (
                f"Bạn là chuyên gia phân tích chứng khoán Việt Nam.\n"
                f"Dữ liệu thực tế hôm nay:\n{context}\n\n"
                f"Hãy phân tích ngắn gọn (3-5 câu mỗi mục):\n"
                f"1. Đánh giá xu hướng ngắn hạn\n"
                f"2. Rủi ro cần chú ý\n"
                f"3. Khuyến nghị: Mua / Giữ / Bán và lý do"
            )

            llm_result = self.llm.generate(prompt)

            return {
                "symbol": normalized_symbol,
                "status": "success",
                "info": info,
                "quote": quote,
                "circuit_breaker": cb_status,
                "tech_summary": tech_summary,
                "history_rows": len(df),
                "llm_analysis": llm_result
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {"symbol": symbol, "error": str(e), "status": "failed"}
