from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class BaseDataProvider(ABC):
    """Abstract data provider cho vn_stock_daily_analysis"""

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Lấy thông tin cơ bản của cổ phiếu (Tên, sàn, nhóm ngành)"""
        pass

    @abstractmethod
    def get_historical_data(
            self,
            symbol: str,
            start: str,
            end: str) -> pd.DataFrame:
        """Lấy dữ liệu OHLCV lịch sử"""
        pass

    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """Lấy giá hiện tại, thay đổi, khối lượng"""
        pass

    @abstractmethod
    def get_financial_report(self, symbol: str) -> Dict[str, Any]:
        """Lấy báo cáo tài chính tóm tắt"""
        pass

    @abstractmethod
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Lấy hồ sơ doanh nghiệp"""
        pass

    @abstractmethod
    def get_financials_bundle(self, symbol: str, years: int = 5) -> Dict[str, Any]:
        """
        Trả dict chứa:
        {
            "income_statement": DataFrame (năm),
            "cash_flow": DataFrame (năm),
            "balance_sheet": DataFrame (năm),
            "ratios": DataFrame (năm),    # ROE, ROA, debt/equity, ...
            "shares_outstanding": float,
            "currency": "VND"
        }
        Ít nhất `years` năm gần nhất, sắp xếp cũ → mới.
        """
        pass
