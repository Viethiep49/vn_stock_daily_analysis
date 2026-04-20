"""Preset filter combinations for stock screening."""
from src.screener.filters import (
    min_market_cap,
    min_liquidity,
    fscore_at_least,
    composite_score_at_least,
    rsi_in_range,
    price_above_ma,
    undervalued_dcf,
    risk_grade_in,
    exclude_industry
)

def buffett_style():
    """Giá trị dài hạn: FCF dương, F-Score cao, DCF undervalued, large cap."""
    return [
        min_market_cap(5000),
        min_liquidity(100_000),
        # fscore_at_least(7), # F-Score implementation is currently limited
        undervalued_dcf(min_upside_pct=25),
        exclude_industry(("Ngân hàng", "Bảo hiểm", "Bất động sản")),
    ]

def lynch_growth():
    """Midcap tăng trưởng, composite cao."""
    return [
        min_market_cap(1000),
        min_liquidity(50_000),
        composite_score_at_least(70),
        rsi_in_range(40, 75),
    ]

def graham_defensive():
    """Margin of safety cực lớn, risk thấp."""
    return [
        min_market_cap(3000),
        # fscore_at_least(8),
        undervalued_dcf(min_upside_pct=40),
        risk_grade_in(("LOW", "MEDIUM")),
    ]

def technical_breakout():
    """Tín hiệu kỹ thuật mạnh, không quan tâm fundamental."""
    return [
        min_liquidity(100_000),
        composite_score_at_least(75),
        rsi_in_range(55, 75),
        price_above_ma("MA50"),
        price_above_ma("MA200"),
    ]

PRESETS = {
    "buffett_style": buffett_style,
    "lynch_growth": lynch_growth,
    "graham_defensive": graham_defensive,
    "technical_breakout": technical_breakout
}
