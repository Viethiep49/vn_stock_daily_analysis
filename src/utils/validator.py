"""
validator.py — Utility để validate và chuẩn hóa mã chứng khoán Việt Nam
"""
import re
from typing import Optional, Tuple
from enum import Enum


class Exchange(Enum):
    HOSE = "HO"
    HNX = "HN"
    UPCOM = "UP"


class VNStockValidator:
    """Validator cho mã chứng khoán Việt Nam"""

    # Pattern: ABC hoặc ABC.HO / ABC.HN / ABC.UP
    SYMBOL_PATTERN = re.compile(
        r'^([A-Z0-9]{1,4})(?:\.(' + '|'.join([e.value for e in Exchange]) + r'))?$',
        re.IGNORECASE
    )

    # Danh sách mã đặc biệt (ETF, chứng quyền, trái phiếu...)
    SPECIAL_PREFIXES = ['E', 'F', 'CW', 'TP', 'CB']

    @classmethod
    def validate(cls, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Validate mã chứng khoán
        Returns: (is_valid, error_message)
        """
        if symbol is None:
            return False, "Symbol cannot be None"
        symbol = str(symbol).strip().upper()

        if not symbol:
            return False, "Symbol cannot be empty"

        match = cls.SYMBOL_PATTERN.match(symbol)
        if not match:
            return False, f"Invalid VN stock format: {symbol}. Expected: VNM, FPT.HO, VCB.HN"

        code, exchange = match.groups()

        # Check special prefixes
        if any(code.startswith(prefix) for prefix in cls.SPECIAL_PREFIXES):
            return True, None  # Allow but log warning

        return True, None

    @classmethod
    def normalize(
            cls,
            symbol: str,
            default_exchange: Exchange = Exchange.HOSE) -> str:
        """
        Chuẩn hóa mã: vnm → VNM.HO, fpt.hn → FPT.HN
        """
        symbol = symbol.strip().upper()
        match = cls.SYMBOL_PATTERN.match(symbol)

        if not match:
            raise ValueError(f"Cannot normalize invalid symbol: {symbol}")

        code, exchange = match.groups()
        exchange = exchange or default_exchange.value

        return f"{code}.{exchange}"

    @classmethod
    def is_bluechip(cls, symbol: str) -> bool:
        """Kiểm tra mã có thuộc VN30/VN Diamond không"""
        VN30_LIST = {
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
        code = symbol.split('.')[0].upper()
        return code in VN30_LIST
