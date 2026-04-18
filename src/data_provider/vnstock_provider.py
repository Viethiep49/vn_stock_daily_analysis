"""
vnstock_provider.py — Data provider sử dụng vnstock v3.5+ (nguồn KBS - miễn phí)
Tài liệu: https://vnstocks.com/docs
"""
import os
import logging
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta

from .base import BaseDataProvider

# Suppress vnstock promotional banners
os.environ.setdefault('VNSTOCK_SHOW_LOG', '0')

logger = logging.getLogger(__name__)


class VNStockProvider(BaseDataProvider):
    """Data provider sử dụng vnstock v3.5+ với nguồn KBS"""

    DEFAULT_SOURCE = 'KBS'

    def __init__(self, source: str = DEFAULT_SOURCE):
        self.source = source
        self._client_cache: Dict[str, Any] = {}
        logger.info(f"VNStockProvider khởi tạo với source={source}")

    def _get_client(self, symbol: str):
        """Lazy-load & cache Vnstock client per symbol"""
        if symbol not in self._client_cache:
            try:
                from vnstock import Vnstock
                self._client_cache[symbol] = Vnstock().stock(symbol=symbol, source=self.source)
            except ImportError:
                raise RuntimeError("vnstock chưa được cài. Chạy: pip install vnstock")
        return self._client_cache[symbol]

    def _clean_symbol(self, symbol: str) -> str:
        """VNM.HO → VNM"""
        return symbol.split('.')[0].upper()

    # ─── Interface Methods ────────────────────────────────────────────────────

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Lấy thông tin cơ bản: sàn, địa chỉ, loại công ty"""
        raw = self._clean_symbol(symbol)
        try:
            client = self._get_client(raw)
            ov = client.company.overview()
            row = ov.iloc[0].to_dict()

            # KBS company.overview() không có company_name → lấy từ listing
            name = raw
            try:
                listing = client.listing.symbols_by_exchange()
                match = listing[listing['symbol'] == raw]
                if not match.empty:
                    name = match.iloc[0].get('organ_name', raw)
            except Exception:
                pass

            return {
                "symbol": raw,
                "exchange": row.get('exchange', 'HOSE'),
                "company_name": name,
                "company_type": row.get('company_type', ''),
                "industry": row.get('industry', '') or row.get('industry_name', ''),
                "website": row.get('website', ''),
                "address": row.get('address', ''),
                "employees": row.get('number_of_employees', None),
                "outstanding_shares": row.get('outstanding_shares', None),
            }
        except Exception as e:
            logger.warning(f"get_stock_info lỗi cho {raw}: {e}. Trả về fallback.")
            return {
                "symbol": raw,
                "exchange": "HOSE",
                "company_name": f"{raw} Corp",
                "industry": "N/A",
                "source": "fallback"
            }

    def get_historical_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Lấy dữ liệu OHLCV theo ngày từ KBS"""
        raw = self._clean_symbol(symbol)
        try:
            client = self._get_client(raw)
            df = client.quote.history(start=start, end=end)
            if df is None or df.empty:
                logger.warning(f"Không có dữ liệu lịch sử cho {raw} ({start} → {end})")
                return pd.DataFrame()

            # Chuẩn hoá tên cột
            df = df.rename(columns={'time': 'date'})
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.sort_values('date').reset_index(drop=True)
            logger.info(f"Lấy {len(df)} rows lịch sử cho {raw}")
            return df

        except Exception as e:
            logger.error(f"get_historical_data lỗi cho {raw}: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Lấy giá mới nhất bằng cách lấy 5 phiên gần đây nhất.
        KBS không có realtime endpoint, dùng close ngày hôm qua.
        """
        raw = self._clean_symbol(symbol)
        try:
            today = datetime.today().strftime('%Y-%m-%d')
            week_ago = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
            df = self.get_historical_data(raw, week_ago, today)

            if df.empty:
                return {"symbol": raw, "price": 0, "change": 0, "volume": 0}

            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else latest

            price = float(latest.get('close', 0))
            prev_close = float(prev.get('close', price))
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            return {
                "symbol": raw,
                "price": price,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": int(latest.get('volume', 0)),
                "open": float(latest.get('open', 0)),
                "high": float(latest.get('high', 0)),
                "low": float(latest.get('low', 0)),
                "date": str(latest.get('date', today)),
            }
        except Exception as e:
            logger.error(f"get_realtime_quote lỗi cho {raw}: {e}")
            return {"symbol": raw, "price": 0, "change": 0, "volume": 0}

    def get_financial_report(self, symbol: str) -> Dict[str, Any]:
        """Lấy báo cáo tài chính tóm tắt (Income Statement)"""
        raw = self._clean_symbol(symbol)
        try:
            client = self._get_client(raw)
            fin = client.finance.income_statement(period='quarter')
            if fin is None or fin.empty:
                return {}
            row = fin.head(1).to_dict(orient='records')[0]
            return {"symbol": raw, "period": "quarter", "data": row}
        except Exception as e:
            logger.warning(f"get_financial_report lỗi cho {raw}: {e}")
            return {}

    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Lấy hồ sơ doanh nghiệp"""
        return self.get_stock_info(symbol)
