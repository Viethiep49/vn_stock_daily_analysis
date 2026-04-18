"""Signal enum used by strategies and the final aggregated report."""
from enum import Enum


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    BUY_WEAK = "BUY_WEAK"
    NEUTRAL = "NEUTRAL"
    SELL_WEAK = "SELL_WEAK"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


def composite_to_signal(score: float) -> Signal:
    """Map composite score 0-100 to the 5-level final signal bucket.

    80-100 → STRONG_BUY
    65-79  → BUY
    40-64  → NEUTRAL
    20-39  → SELL
    0-19   → STRONG_SELL
    """
    if score < 0 or score > 100:
        raise ValueError(f"score must be in [0, 100], got {score}")
    if score >= 80:
        return Signal.STRONG_BUY
    if score >= 65:
        return Signal.BUY
    if score >= 40:
        return Signal.NEUTRAL
    if score >= 20:
        return Signal.SELL
    return Signal.STRONG_SELL
