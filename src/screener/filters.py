"""Filter primitives for stock screening."""
from typing import Callable, Tuple

def min_market_cap(bn_vnd: float) -> Callable[[dict], bool]:
    return lambda r: (r.get("market_cap_bn") or 0) >= bn_vnd

def min_liquidity(shares_per_day: float) -> Callable[[dict], bool]:
    return lambda r: (r.get("avg_volume_20d") or 0) >= shares_per_day

def fscore_at_least(threshold: int) -> Callable[[dict], bool]:
    return lambda r: (r.get("f_score") or 0) >= threshold

def composite_score_at_least(threshold: float) -> Callable[[dict], bool]:
    return lambda r: (r.get("composite_score") or 0) >= threshold

def rsi_in_range(lo: float, hi: float) -> Callable[[dict], bool]:
    return lambda r: lo <= (r.get("RSI14") or 0) <= hi

def price_above_ma(ma_key: str) -> Callable[[dict], bool]:
    return lambda r: (r.get("close") or 0) > (r.get(ma_key) or float("inf"))

def undervalued_dcf(min_upside_pct: float = 20) -> Callable[[dict], bool]:
    return lambda r: (r.get("dcf_upside_pct") or -999) >= min_upside_pct

def risk_grade_in(grades: Tuple[str, ...]) -> Callable[[dict], bool]:
    return lambda r: r.get("risk_grade") in grades

def industry_in(industries: Tuple[str, ...]) -> Callable[[dict], bool]:
    return lambda r: r.get("industry") in industries

def exclude_industry(industries: Tuple[str, ...]) -> Callable[[dict], bool]:
    return lambda r: r.get("industry") not in industries
