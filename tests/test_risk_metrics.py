import unittest
import pandas as pd
import numpy as np
from src.scoring.risk_metrics import RiskEngine, RiskMetrics

class TestRiskMetrics(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine(risk_free_rate=0.045)

    def test_sufficient_data(self):
        # 300 days of random returns around 0.02% daily
        np.random.seed(42)
        returns = np.random.normal(0.0002, 0.01, 300)
        prices = 100 * (1 + returns).cumprod()
        df = pd.DataFrame({
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': [1000] * 300
        })
        
        metrics = self.engine.compute(df)
        
        self.assertIsNotNone(metrics.volatility_annual)
        self.assertIsNotNone(metrics.sharpe_ratio)
        self.assertIsNotNone(metrics.sortino_ratio)
        self.assertIsNotNone(metrics.var_95_1d)
        self.assertIsNotNone(metrics.cvar_95_1d)
        self.assertIsNotNone(metrics.max_drawdown)
        self.assertIsNotNone(metrics.current_drawdown)
        self.assertIn(metrics.risk_grade, ["LOW", "MEDIUM", "HIGH", "EXTREME"])
        self.assertNotEqual(metrics.risk_grade, "UNKNOWN")

    def test_insufficient_data(self):
        df = pd.DataFrame({'close': [100] * 30})
        metrics = self.engine.compute(df)
        
        self.assertEqual(metrics.risk_grade, "UNKNOWN")
        self.assertIsNone(metrics.volatility_annual)

    def test_constant_price(self):
        # 100 days of constant price
        df = pd.DataFrame({
            'close': [100.0] * 100,
            'open': [100.0] * 100,
            'high': [100.0] * 100,
            'low': [100.0] * 100,
            'volume': [1000] * 100
        })
        metrics = self.engine.compute(df)
        
        self.assertEqual(metrics.volatility_annual, 0.0)
        self.assertEqual(metrics.max_drawdown, 0.0)
        self.assertEqual(metrics.risk_grade, "LOW")

    def test_declining_price(self):
        # Price declining by 1% each day
        prices = [100 * (0.99 ** i) for i in range(100)]
        df = pd.DataFrame({
            'close': prices,
            'open': prices,
            'high': prices,
            'low': prices,
            'volume': [1000] * 100
        })
        metrics = self.engine.compute(df)
        
        self.assertLess(metrics.max_drawdown, 0.0)
        self.assertAlmostEqual(metrics.current_drawdown, metrics.max_drawdown)

if __name__ == '__main__':
    unittest.main()
