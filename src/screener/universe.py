"""Lấy universe mã chứng khoán VN + metadata (ngành, market cap, liquidity)."""
import os
import logging
import pandas as pd
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime, date

logger = logging.getLogger(__name__)

@dataclass
class UniverseItem:
    symbol: str
    exchange: str           # HOSE | HNX | UPCOM
    company_name: str
    industry: str
    market_cap_bn: Optional[float] = None   # Tỷ VND
    avg_volume_20d: Optional[float] = None  # Khớp lệnh bình quân

class UniverseLoader:
    """
    Load + cache file .cache/universe_{date}.parquet để tránh spam vnstock.
    TTL 24h. Nếu cache miss hoặc hết hạn → fetch mới.
    """
    CACHE_DIR = ".cache"

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def load(self, exchanges: Tuple[str, ...] = ("HOSE", "HNX")) -> List[UniverseItem]:
        today_str = date.today().strftime("%Y%m%d")
        cache_path = os.path.join(self.cache_dir, f"universe_{today_str}.parquet")

        if os.path.exists(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                logger.info(f"Loaded universe from cache: {cache_path}")
                return self._df_to_items(df[df['exchange'].isin(exchanges)])
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_path}: {e}")

        # Fetch new data
        all_items = []
        for ex in exchanges:
            try:
                items = self._fetch_from_vnstock(ex)
                all_items.extend(items)
            except Exception as e:
                logger.error(f"Failed to fetch universe for {ex}: {e}")

        if all_items:
            df = pd.DataFrame([item.__dict__ for item in all_items])
            try:
                df.to_parquet(cache_path)
                logger.info(f"Saved universe to cache: {cache_path}")
            except Exception as e:
                logger.warning(f"Failed to save cache {cache_path}: {e}")
        
        return [item for item in all_items if item.exchange in exchanges]

    def _fetch_from_vnstock(self, exchange: str) -> List[UniverseItem]:
        """Fetch symbol list + basic info from vnstock."""
        from vnstock import Vnstock
        
        # vnstock v3.5+
        stock = Vnstock().stock(symbol="VNM", source="KBS") # Dummy symbol to get the client
        listing = stock.listing.symbols_by_exchange()
        
        # Filter by exchange
        df = listing[listing['exchange'] == exchange]
        
        items = []
        for _, row in df.iterrows():
            items.append(UniverseItem(
                symbol=row['symbol'],
                exchange=row['exchange'],
                company_name=row.get('organ_name', row['symbol']),
                industry=row.get('industry_name', 'N/A'),
                market_cap_bn=None, # Will be fetched later if needed or in screener
                avg_volume_20d=None
            ))
        
        logger.info(f"Fetched {len(items)} symbols for {exchange} from vnstock")
        return items

    def _df_to_items(self, df: pd.DataFrame) -> List[UniverseItem]:
        items = []
        for _, row in df.iterrows():
            items.append(UniverseItem(**row.to_dict()))
        return items
