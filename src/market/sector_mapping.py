from typing import Dict, List


class SectorMapping:
    """ICB (Industry Classification Benchmark) Vietnam Sector Mapping"""

    # Simple dictionary for common stocks and their sectors
    # In reality, this should be fetched or cached from a database or API
    _MAPPING: Dict[str, str] = {
        "VCB": "Ngân hàng",
        "BID": "Ngân hàng",
        "CTG": "Ngân hàng",
        "TCB": "Ngân hàng",
        "MBB": "Ngân hàng",
        "VHM": "Bất động sản",
        "VIC": "Bất động sản",
        "VRE": "Bất động sản",
        "HPG": "Thép",
        "HSG": "Thép",
        "NKG": "Thép",
        "SSI": "Chứng khoán",
        "VND": "Chứng khoán",
        "GAS": "Dầu khí",
        "PVD": "Dầu khí",
        "MWG": "Bán lẻ",
        "PNJ": "Bán lẻ",
        "FRT": "Bán lẻ",
        "FPT": "CNTT",
        "VNM": "Thực phẩm",
        "MSN": "Thực phẩm",
        "SAB": "Thực phẩm"
    }

    @classmethod
    def get_sector(cls, symbol: str) -> str:
        """Lấy tên ngành của một cổ phiếu"""
        # Clean symbol (e.g. VNM.HO -> VNM)
        clean_symbol = symbol.split('.')[0].upper()
        return cls._MAPPING.get(clean_symbol, "Ngành Khác")

    @classmethod
    def get_stocks_in_sector(cls, sector: str) -> List[str]:
        """Lấy danh sách mã chứng khoán trong một ngành"""
        return [sym for sym, sec in cls._MAPPING.items() if sec.lower()
                == sector.lower()]
