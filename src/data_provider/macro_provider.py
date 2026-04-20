"""Macro overlay: Fed Funds Rate, DXY, US Treasury yields, VIX từ FRED (public CSV)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import requests
import pandas as pd
from io import StringIO
import os

logger = logging.getLogger(__name__)


@dataclass
class MacroSnapshot:
    as_of: str                          # ISO date
    fed_funds_rate: Optional[float]     # %
    fed_funds_rate_delta_30d: Optional[float]  # điểm % thay đổi 30 ngày
    dxy: Optional[float]                # US Dollar Index
    dxy_delta_30d_pct: Optional[float]  # % thay đổi 30 ngày
    us10y: Optional[float]              # %
    us2y: Optional[float]               # %
    yield_curve_10y_2y: Optional[float] # US10Y - US2Y (điểm %)
    vix: Optional[float]
    regime: str                         # "RISK_ON" | "RISK_OFF" | "NEUTRAL"
    notes: List[str]                    # Danh sách cảnh báo macro cho thị trường VN


class FREDMacroProvider:
    """
    Lấy dữ liệu FRED qua public CSV endpoint (không cần key).
    Có cache đơn giản in-memory + tuỳ chọn cache file để tránh spam FRED.
    """
    BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    SERIES = {
        "fed_funds_rate": "DFF",
        "dxy": "DTWEXBGS",
        "us10y": "DGS10",
        "us2y": "DGS2",
        "vix": "VIXCLS",
    }
    CACHE_DIR = ".cache"

    def __init__(self, cache_ttl_hours: int = 6, timeout: int = 10):
        self._cache: Dict[str, tuple] = {}  # series_id -> (ts, df)
        self.ttl = timedelta(hours=cache_ttl_hours)
        self.timeout = timeout
        
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

    def _fetch_series(self, series_id: str) -> pd.DataFrame:
        """Fetch + cache một series. Trả DataFrame với cột date, value."""
        now = datetime.now()
        
        # 1. Check in-memory cache
        if series_id in self._cache:
            ts, df = self._cache[series_id]
            if now - ts < self.ttl:
                return df
        
        # 2. Check file cache
        cache_file = os.path.join(self.CACHE_DIR, f"fred_{series_id}.parquet")
        if os.path.exists(cache_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if now - mtime < self.ttl:
                try:
                    df = pd.read_parquet(cache_file)
                    self._cache[series_id] = (mtime, df)
                    return df
                except Exception as e:
                    logger.warning(f"Failed to read cache file {cache_file}: {e}")

        # 3. Fetch from FRED
        try:
            logger.info(f"Fetching {series_id} from FRED...")
            params = {"id": series_id}
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            df.columns = ['date', 'value']
            # FRED uses '.' for missing values in CSV
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df['date'] = pd.to_datetime(df['date'])
            df = df.dropna().sort_values('date')
            
            # Save to cache
            self._cache[series_id] = (now, df)
            df.to_parquet(cache_file)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching {series_id} from FRED: {e}")
            return pd.DataFrame(columns=['date', 'value'])

    def get_snapshot(self) -> MacroSnapshot:
        """Gộp tất cả series → MacroSnapshot, xác định regime."""
        data = {}
        for key, series_id in self.SERIES.items():
            df = self._fetch_series(series_id)
            data[key] = df

        snapshot_data = {
            "as_of": datetime.now().strftime("%Y-%m-%d"),
            "fed_funds_rate": None,
            "fed_funds_rate_delta_30d": None,
            "dxy": None,
            "dxy_delta_30d_pct": None,
            "us10y": None,
            "us2y": None,
            "yield_curve_10y_2y": None,
            "vix": None,
            "regime": "NEUTRAL",
            "notes": []
        }

        # Calculate values
        try:
            # Fed Funds Rate
            df_ff = data["fed_funds_rate"]
            if not df_ff.empty:
                current_ff = df_ff.iloc[-1]['value']
                snapshot_data["fed_funds_rate"] = current_ff
                
                # Delta 30d
                date_30d_ago = df_ff.iloc[-1]['date'] - timedelta(days=30)
                df_30d = df_ff[df_ff['date'] <= date_30d_ago]
                if not df_30d.empty:
                    ff_30d = df_30d.iloc[-1]['value']
                    snapshot_data["fed_funds_rate_delta_30d"] = current_ff - ff_30d

            # DXY
            df_dxy = data["dxy"]
            if not df_dxy.empty:
                current_dxy = df_dxy.iloc[-1]['value']
                snapshot_data["dxy"] = current_dxy
                
                # Delta 30d %
                date_30d_ago = df_dxy.iloc[-1]['date'] - timedelta(days=30)
                df_30d = df_dxy[df_dxy['date'] <= date_30d_ago]
                if not df_30d.empty:
                    dxy_30d = df_30d.iloc[-1]['value']
                    snapshot_data["dxy_delta_30d_pct"] = (current_dxy - dxy_30d) / dxy_30d * 100

            # Yields
            df_10y = data["us10y"]
            df_2y = data["us2y"]
            if not df_10y.empty:
                snapshot_data["us10y"] = df_10y.iloc[-1]['value']
            if not df_2y.empty:
                snapshot_data["us2y"] = df_2y.iloc[-1]['value']
            
            if snapshot_data["us10y"] is not None and snapshot_data["us2y"] is not None:
                snapshot_data["yield_curve_10y_2y"] = snapshot_data["us10y"] - snapshot_data["us2y"]

            # VIX
            df_vix = data["vix"]
            if not df_vix.empty:
                snapshot_data["vix"] = df_vix.iloc[-1]['value']

            # Regime Classification
            vix = snapshot_data["vix"]
            curve = snapshot_data["yield_curve_10y_2y"]
            dxy_pct = snapshot_data["dxy_delta_30d_pct"]
            
            if vix is not None and curve is not None and dxy_pct is not None:
                if vix > 25 or curve < 0 or dxy_pct > 2:
                    snapshot_data["regime"] = "RISK_OFF"
                elif vix < 15 and curve > 0.5 and dxy_pct < -1:
                    snapshot_data["regime"] = "RISK_ON"
                else:
                    snapshot_data["regime"] = "NEUTRAL"
            
            # VN Notes
            notes = []
            if dxy_pct is not None and dxy_pct > 1.5:
                notes.append("DXY tăng → áp lực rút vốn ngoại khỏi HOSE")
            if snapshot_data["fed_funds_rate_delta_30d"] is not None and snapshot_data["fed_funds_rate_delta_30d"] > 0.25:
                notes.append("Fed thắt chặt → SBV có thể phải nâng lãi suất theo")
            if curve is not None and curve < 0:
                notes.append("Yield curve đảo ngược → tín hiệu suy thoái Mỹ, VN thường chịu ảnh hưởng trễ 6–9 tháng")
            if vix is not None and vix > 30:
                notes.append("VIX cao → risk-off toàn cầu, tránh midcap/penny VN")
            
            if not notes and any(v is None for v in [vix, curve, dxy_pct]):
                notes.append("Macro data partially unavailable")
                
            snapshot_data["notes"] = notes

        except Exception as e:
            logger.error(f"Error calculating macro snapshot: {e}")
            snapshot_data["notes"] = ["Macro data calculation error"]

        # Fallback if everything failed
        if all(v is None for v in [snapshot_data["fed_funds_rate"], snapshot_data["dxy"], snapshot_data["vix"]]):
            snapshot_data["notes"] = ["Macro data unavailable"]
            snapshot_data["regime"] = "NEUTRAL"

        return MacroSnapshot(**snapshot_data)
