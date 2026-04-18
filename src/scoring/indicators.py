"""Centralized indicator computation. Returns an IndicatorSet snapshot."""
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import pandas_ta_classic as ta


class InsufficientDataError(ValueError):
    """Raised when OHLCV data has too few rows for the indicators we need."""


@dataclass
class IndicatorSet:
    # Price
    close: float
    prev_close: float
    # Moving averages (SMA)
    MA5: Optional[float]
    MA10: Optional[float]
    MA20: Optional[float]
    MA50: Optional[float]
    MA200: Optional[float]
    prev_MA5: Optional[float]
    prev_MA20: Optional[float]
    prev_MA50: Optional[float]
    # Momentum
    RSI14: Optional[float]
    prev_RSI14: Optional[float]
    MACD: Optional[float]
    MACD_signal: Optional[float]
    MACD_hist: Optional[float]
    prev_MACD_hist: Optional[float]
    # Volatility
    BB_upper: Optional[float]
    BB_mid: Optional[float]
    BB_lower: Optional[float]
    ATR14: Optional[float]
    # Volume
    volume: float
    volume_ma20: Optional[float]
    volume_ratio: Optional[float]
    # Price structure
    support_20: Optional[float]
    resistance_20: Optional[float]


class IndicatorEngine:
    MIN_ROWS = 50  # enough for MA50 + comparison to previous row

    def compute(self, df: pd.DataFrame) -> IndicatorSet:
        if len(df) < self.MIN_ROWS:
            raise InsufficientDataError(
                f"Need at least {self.MIN_ROWS} rows, got {len(df)}"
            )

        df = df.copy().reset_index(drop=True)
        close = df["close"].astype(float)
        volume = df["volume"].astype(float)

        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean() if len(df) >= 200 else pd.Series([None] * len(df))

        rsi = ta.rsi(close, length=14)

        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        # pandas-ta columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        macd = macd_df.iloc[:, 0] if macd_df is not None else pd.Series([None] * len(df))
        macd_hist = macd_df.iloc[:, 1] if macd_df is not None else pd.Series([None] * len(df))
        macd_signal = macd_df.iloc[:, 2] if macd_df is not None else pd.Series([None] * len(df))

        bb = ta.bbands(close, length=20, std=2)
        # pandas-ta columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, ...
        bb_lower = bb.iloc[:, 0] if bb is not None else pd.Series([None] * len(df))
        bb_mid = bb.iloc[:, 1] if bb is not None else pd.Series([None] * len(df))
        bb_upper = bb.iloc[:, 2] if bb is not None else pd.Series([None] * len(df))

        atr = ta.atr(df["high"].astype(float), df["low"].astype(float), close, length=14)

        vol_ma20 = volume.rolling(20).mean()

        last = len(df) - 1
        prev = last - 1

        last_ma20 = _val(ma20, last)
        last_vol_ma20 = _val(vol_ma20, last)

        return IndicatorSet(
            close=float(close.iloc[last]),
            prev_close=float(close.iloc[prev]),
            MA5=_val(ma5, last),
            MA10=_val(ma10, last),
            MA20=last_ma20,
            MA50=_val(ma50, last),
            MA200=_val(ma200, last) if ma200 is not None else None,
            prev_MA5=_val(ma5, prev),
            prev_MA20=_val(ma20, prev),
            prev_MA50=_val(ma50, prev),
            RSI14=_val(rsi, last),
            prev_RSI14=_val(rsi, prev),
            MACD=_val(macd, last),
            MACD_signal=_val(macd_signal, last),
            MACD_hist=_val(macd_hist, last),
            prev_MACD_hist=_val(macd_hist, prev),
            BB_upper=_val(bb_upper, last),
            BB_mid=_val(bb_mid, last),
            BB_lower=_val(bb_lower, last),
            ATR14=_val(atr, last),
            volume=float(volume.iloc[last]),
            volume_ma20=last_vol_ma20,
            volume_ratio=(float(volume.iloc[last]) / last_vol_ma20) if last_vol_ma20 else None,
            support_20=float(close.tail(20).min()),
            resistance_20=float(close.tail(20).max()),
        )


def _val(series, idx):
    """Return float(series[idx]) or None if NaN / out of range."""
    if series is None or idx < 0 or idx >= len(series):
        return None
    v = series.iloc[idx] if hasattr(series, "iloc") else series[idx]
    if v is None or pd.isna(v):
        return None
    return float(v)
