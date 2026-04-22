"""DCF intrinsic value + valuation grade."""
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class DCFAssumptions:
    growth_high: float = 0.15        # Giai đoạn tăng trưởng mạnh (năm 1-5), 15%/năm
    growth_terminal: float = 0.03    # Tăng trưởng vĩnh viễn, 3%/năm
    discount_rate: float = 0.12      # WACC giả định cho VN
    years_high_growth: int = 5
    years_fade: int = 5              # 5 năm fade từ growth_high → growth_terminal

@dataclass
class ValuationResult:
    intrinsic_value_per_share: Optional[float] = None  # VND
    market_price: float = 0.0                          # VND
    upside_pct: Optional[float] = None                 # (intrinsic - market) / market * 100
    margin_of_safety_pct: Optional[float] = None       # ≥ 0 mới có ý nghĩa
    fcf_base: Optional[float] = None                   # FCF bình quân 3 năm, làm base
    fcf_trend: str = "N/A"                             # "GROWING" | "STABLE" | "DECLINING" | "NEGATIVE"
    assumptions: DCFAssumptions = field(default_factory=DCFAssumptions)
    grade: str = "N/A"                                 # "UNDERVALUED" | "FAIR" | "OVERVALUED" | "SPECULATIVE"
    notes: List[str] = field(default_factory=list)

class DCFEngine:
    """
    Simple two-stage DCF (high growth → fade → terminal).
    VN-specific defaults: discount_rate 12% (cao hơn US ~8-10% vì country risk premium).
    """

    def __init__(self, assumptions: Optional[DCFAssumptions] = None):
        self.a = assumptions or DCFAssumptions()

    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Tìm cột dựa trên keywords (không phân biệt hoa thường)"""
        for col in df.columns:
            col_lower = str(col).lower()
            if any(kw.lower() in col_lower for kw in keywords):
                return col
        return None

    def compute(
        self,
        financials_bundle: Dict[str, Any],
        market_price_vnd: float,
        industry: Optional[str] = None,
    ) -> ValuationResult:
        result = ValuationResult(market_price=market_price_vnd, assumptions=self.a)
        
        # 1. Check industry
        if industry and any(kw in industry for kw in ["Ngân hàng", "Bảo hiểm", "Chứng khoán", "Banking", "Insurance", "Securities"]):
            result.grade = "SPECULATIVE"
            result.notes.append("DCF không phù hợp cho ngành tài chính — dùng P/B hoặc Dividend Discount Model.")
            return result

        # 2. Extract Data
        cf_df = financials_bundle.get("cash_flow", pd.DataFrame())
        shares = financials_bundle.get("shares_outstanding", 0)

        if cf_df.empty:
            result.grade = "SPECULATIVE"
            result.notes.append("Thiếu dữ liệu Cash Flow để tính FCF.")
            return result
        
        if not shares or shares <= 0:
            result.grade = "SPECULATIVE"
            result.notes.append("Không có thông tin số lượng cổ phiếu lưu hành.")
            return result

        # 3. Calculate Historical FCF
        # Keywords cho vnstock v3 (KBS source)
        # OCF: "Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh"
        # CapEx: "Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác"
        ocf_col = self._find_column(cf_df, ["Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh", "Operating Activities", "từ hoạt động kinh doanh"])
        capex_col = self._find_column(cf_df, ["Tiền chi để mua sắm, xây dựng TSCĐ", "purchase, construct PPE", "mua sắm, xây dựng TSCĐ"])

        if not ocf_col:
            result.grade = "SPECULATIVE"
            result.notes.append("Không tìm thấy cột Operating Cash Flow.")
            return result
        
        # CapEx is often negative in cash flow statements, but we should check.
        # If we can't find capex, we might assume 0 or try to find it in Investing Activities.
        historical_fcf = []
        for _, row in cf_df.iterrows():
            ocf = row[ocf_col]
            capex = row[capex_col] if capex_col else 0
            # CapEx thường là số âm trong báo cáo, ta cần giá trị tuyệt đối để trừ OCF
            # Hoặc cộng nếu nó đã âm. Giả sử: FCF = OCF + CapEx (nếu CapEx âm)
            fcf = ocf + capex if capex is not None else ocf
            historical_fcf.append(fcf)
        
        if not historical_fcf:
            result.grade = "SPECULATIVE"
            result.notes.append("Dữ liệu FCF lịch sử trống.")
            return result

        # 4. Analyze FCF
        last_3_fcf = historical_fcf[-3:]
        fcf_base = sum(last_3_fcf) / len(last_3_fcf)
        result.fcf_base = fcf_base

        if all(f < 0 for f in last_3_fcf):
            result.grade = "SPECULATIVE"
            result.fcf_trend = "NEGATIVE"
            result.notes.append("FCF âm liên tục trong 3 năm gần nhất, không định giá được bằng DCF.")
            return result
        
        # Trend
        if len(last_3_fcf) >= 2:
            is_growing = all(last_3_fcf[i] < last_3_fcf[i+1] for i in range(len(last_3_fcf)-1))
            is_declining = all(last_3_fcf[i] > last_3_fcf[i+1] for i in range(len(last_3_fcf)-1))
            
            variation = (max(last_3_fcf) - min(last_3_fcf)) / abs(fcf_base) if fcf_base != 0 else 0
            
            if is_growing:
                result.fcf_trend = "GROWING"
            elif is_declining:
                result.fcf_trend = "DECLINING"
            elif variation < 0.2:
                result.fcf_trend = "STABLE"
            else:
                result.fcf_trend = "VOLATILE"
        
        if any(f < 0 for f in last_3_fcf):
            result.notes.append("Cảnh báo: Có năm FCF bị âm trong giai đoạn gần đây.")

        # 5. Adjusted Assumptions for VN
        # Market cap check
        market_cap = market_price_vnd * shares
        if market_cap < 1_000_000_000_000: # < 1000 tỷ VND
            self.a.discount_rate = 0.14
            result.notes.append("Điều chỉnh Discount Rate lên 14% do vốn hoá nhỏ (< 1000 tỷ).")

        # 6. Project FCF
        # Two-stage: High Growth (1-5) -> Fade (6-10) -> Terminal
        r = self.a.discount_rate
        gh = self.a.growth_high
        gt = self.a.growth_terminal
        
        pv_fcf = 0
        current_fcf = fcf_base
        
        # Growth phase
        for t in range(1, self.a.years_high_growth + 1):
            current_fcf *= (1 + gh)
            pv_fcf += current_fcf / ((1 + r) ** t)
        
        # Fade phase
        for t in range(self.a.years_high_growth + 1, self.a.years_high_growth + self.a.years_fade + 1):
            # Linear fade growth rate
            years_into_fade = t - self.a.years_high_growth
            current_growth = gh - (gh - gt) * (years_into_fade / self.a.years_fade)
            current_fcf *= (1 + current_growth)
            pv_fcf += current_fcf / ((1 + r) ** t)
            
        # Terminal Value
        tv = (current_fcf * (1 + gt)) / (r - gt)
        pv_tv = tv / ((1 + r) ** (self.a.years_high_growth + self.a.years_fade))
        
        total_pv = pv_fcf + pv_tv
        intrinsic_value = total_pv / shares
        
        result.intrinsic_value_per_share = intrinsic_value
        
        # 7. Valuation and Grade
        if market_price_vnd > 0:
            upside = (intrinsic_value - market_price_vnd) / market_price_vnd * 100
            result.upside_pct = upside
            result.margin_of_safety_pct = max(0.0, upside)
            
            if upside >= 30:
                result.grade = "UNDERVALUED"
            elif upside >= -10:
                result.grade = "FAIR"
            else:
                result.grade = "OVERVALUED"
        else:
            result.grade = "N/A"

        return result
