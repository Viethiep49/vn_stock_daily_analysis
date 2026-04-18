"""
circuit_breaker.py — Xử lý logic giá trần/floor của HOSE/HNX/UPCOM
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PriceLimitConfig:
    """Cấu hình biên độ giá theo sàn và nhóm cổ phiếu"""
    hose_bluechip: float = 0.07    # VN30: ±7%
    # HOSE thường: ±7% (VN allows up to 7% limit normally)
    hose_normal: float = 0.07
    hnx: float = 0.10              # HNX: ±10%
    upcom: float = 0.15            # UPCOM: ±15%


class CircuitBreakerHandler:
    """Xử lý cảnh báo và logic khi cổ phiếu chạm trần/sàn"""

    def __init__(self, config: Optional[PriceLimitConfig] = None):
        self.config = config or PriceLimitConfig()
        self._ref_prices: Dict[str, float] = {}

    def set_reference_price(self, symbol: str, ref_price: float):
        """Set giá tham chiếu (giá đóng cửa phiên trước)"""
        self._ref_prices[symbol.upper()] = ref_price

    def get_price_limits(self, symbol: str) -> tuple[float, float]:
        """Tính giá trần/floor cho mã"""
        symbol = symbol.upper()
        if symbol not in self._ref_prices:
            raise ValueError(f"Reference price not set for {symbol}")

        ref = self._ref_prices[symbol]
        code, exchange = symbol.split('.') if '.' in symbol else (symbol, 'HO')

        if exchange == 'HO':
            limit = self.config.hose_bluechip if self._is_bluechip(
                code) else self.config.hose_normal
        elif exchange == 'HN':
            limit = self.config.hnx
        else:
            limit = self.config.upcom

        ceiling = ref * (1 + limit)
        floor = ref * (1 - limit)

        # KBS source trả giá theo nghìn đồng (VD: VNM = 61.3 = 61,300đ)
        # Làm tròn 2 chữ số thập phân phù hợp với đơn vị nghìn đồng
        ceiling = round(ceiling, 1)
        floor = round(floor, 1)

        return ceiling, floor

    def check_limit_status(self, symbol: str, current_price: float) -> dict:
        """Kiểm tra trạng thái giá hiện tại so với trần/floor"""
        ceiling, floor = self.get_price_limits(symbol)

        status = {
            'symbol': symbol,
            'current_price': current_price,
            'ceiling': ceiling,
            'floor': floor,
            'is_limit_up': False,
            'is_limit_down': False,
            'distance_to_ceiling': None,
            'distance_to_floor': None,
            'warning': None
        }

        tolerance = 0.001
        if current_price >= ceiling * (1 - tolerance):
            status['is_limit_up'] = True
            status['warning'] = f"⚠️ {symbol} đang ở giá TRẦN ({ceiling:,.0f}đ) — Khó mua"
        elif current_price <= floor * (1 + tolerance):
            status['is_limit_down'] = True
            status['warning'] = f"⚠️ {symbol} đang ở giá SÀN ({floor:,.0f}đ) — Khó bán"
        else:
            status['distance_to_ceiling'] = round(
                (ceiling - current_price) / current_price * 100, 2)
            status['distance_to_floor'] = round(
                (current_price - floor) / current_price * 100, 2)

        return status

    def _is_bluechip(self, code: str) -> bool:
        VN30_CODES = {
            'VNM',
            'VCB',
            'VHM',
            'VRE',
            'VIC',
            'HPG',
            'FPT',
            'MWG',
            'TCB',
            'MBB',
            'SSI',
            'VND',
            'HCM',
            'GAS',
            'PLX',
            'POW',
            'TPB',
            'ACB',
            'STB',
            'BVH',
            'MSN',
            'VJC',
            'HPX',
            'DCM',
            'PVS',
            'BIM',
            'NT2',
            'GVR',
            'TCH',
            'REE'}
        return code in VN30_CODES
