"""Risk metrics: VaR, Sharpe, Max Drawdown, Volatility — tính từ OHLCV."""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class RiskMetrics:
    volatility_annual: Optional[float]   # %/năm, dựa trên daily returns * sqrt(252)
    sharpe_ratio: Optional[float]        # (mean_ret - rf) / std, annualized
    sortino_ratio: Optional[float]       # Sharpe nhưng dùng downside deviation
    var_95_1d: Optional[float]           # Historical VaR 95% 1 ngày, đơn vị %
    cvar_95_1d: Optional[float]          # Expected Shortfall (CVaR) 95%
    max_drawdown: Optional[float]        # % sụt giảm tối đa từ peak, giá trị âm
    current_drawdown: Optional[float]    # % drawdown tại thời điểm hiện tại
    risk_grade: str                      # "LOW" | "MEDIUM" | "HIGH" | "EXTREME" | "UNKNOWN"


class RiskEngine:
    """
    Tính các chỉ số rủi ro từ OHLCV (cần >= 60 phiên để đáng tin).
    Risk-free rate mặc định 4.5%/năm (xấp xỉ lãi suất kỳ hạn 12T VN).
    """
    MIN_ROWS = 60
    TRADING_DAYS = 252

    def __init__(self, risk_free_rate: float = 0.045):
        self.rf = risk_free_rate

    def compute(self, df: pd.DataFrame) -> RiskMetrics:
        if df is None or len(df) < self.MIN_ROWS:
            return RiskMetrics(
                volatility_annual=None,
                sharpe_ratio=None,
                sortino_ratio=None,
                var_95_1d=None,
                cvar_95_1d=None,
                max_drawdown=None,
                current_drawdown=None,
                risk_grade="UNKNOWN"
            )

        # Use 'close' column for returns
        close = df['close']
        returns = close.pct_change().dropna()
        
        if returns.empty or returns.std() == 0:
            return RiskMetrics(
                volatility_annual=0.0,
                sharpe_ratio=None,
                sortino_ratio=None,
                var_95_1d=0.0,
                cvar_95_1d=0.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                risk_grade="LOW"
            )

        # 1. Volatility
        vol_daily = returns.std()
        volatility_annual = vol_daily * np.sqrt(self.TRADING_DAYS) * 100

        # 2. Sharpe Ratio
        mean_return_daily = returns.mean()
        # Annualized Sharpe = (Mean Annual Return - RF) / Annual Std
        # simplified: (mean_ret * 252 - rf) / (std * sqrt(252))
        sharpe_ratio = (mean_return_daily * self.TRADING_DAYS - self.rf) / (vol_daily * np.sqrt(self.TRADING_DAYS))

        # 3. Sortino Ratio
        downside_returns = returns[returns < 0]
        if not downside_returns.empty:
            downside_std_daily = downside_returns.std()
            sortino_ratio = (mean_return_daily * self.TRADING_DAYS - self.rf) / (downside_std_daily * np.sqrt(self.TRADING_DAYS))
        else:
            sortino_ratio = None

        # 4. VaR 95% 1D
        var_95_1d = np.percentile(returns, 5) * 100

        # 5. CVaR 95% 1D
        cvar_95_1d = returns[returns <= np.percentile(returns, 5)].mean() * 100

        # 6. Drawdown
        cum = (1 + returns).cumprod()
        peak = cum.cummax()
        dd = (cum - peak) / peak
        max_drawdown = dd.min() * 100
        current_drawdown = dd.iloc[-1] * 100

        # 7. Risk Grade
        if volatility_annual < 25:
            risk_grade = "LOW"
        elif volatility_annual < 40:
            risk_grade = "MEDIUM"
        elif volatility_annual < 60:
            risk_grade = "HIGH"
        else:
            risk_grade = "EXTREME"

        return RiskMetrics(
            volatility_annual=volatility_annual,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            var_95_1d=var_95_1d,
            cvar_95_1d=cvar_95_1d,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            risk_grade=risk_grade
        )
