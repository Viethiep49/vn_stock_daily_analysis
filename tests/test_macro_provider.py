import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.data_provider.macro_provider import FREDMacroProvider, MacroSnapshot

class TestFREDMacroProvider(unittest.TestCase):
    def setUp(self):
        self.provider = FREDMacroProvider(cache_ttl_hours=0) # Disable cache for tests

    @patch('requests.get')
    def test_get_snapshot_success(self, mock_get):
        # Mock CSV responses for all 5 series
        # DFF, DTWEXBGS, DGS10, DGS2, VIXCLS
        # Provide enough history to calculate delta
        mock_csv = "date,value\n2023-01-01,5.0\n2023-02-01,5.25"
        mock_response = MagicMock()
        mock_response.text = mock_csv
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        snapshot = self.provider.get_snapshot()
        
        self.assertEqual(snapshot.fed_funds_rate, 5.25)
        self.assertEqual(snapshot.fed_funds_rate_delta_30d, 0.25)
        # dxy_pct = (5.25-5.0)/5.0 * 100 = 5% > 2 -> RISK_OFF
        self.assertEqual(snapshot.regime, "RISK_OFF")
        self.assertTrue(len(snapshot.notes) >= 0)

    @patch('requests.get')
    def test_get_snapshot_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection error")
        
        snapshot = self.provider.get_snapshot()
        
        self.assertEqual(snapshot.regime, "NEUTRAL")
        self.assertIn("Macro data unavailable", snapshot.notes)
        self.assertIsNone(snapshot.fed_funds_rate)

    def test_regime_classification(self):
        # Manually inject data to test logic or mock _fetch_series
        with patch.object(FREDMacroProvider, '_fetch_series') as mock_fetch:
            # RISK_OFF: vix > 25
            def side_effect(series_id):
                # Provide 2 days for all to ensure delta calculation works
                dates = [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')]
                if series_id == "VIXCLS":
                    return pd.DataFrame({'date': dates, 'value': [20.0, 31.0]})
                if series_id == "DGS10":
                    return pd.DataFrame({'date': dates, 'value': [3.0, 3.0]})
                if series_id == "DGS2":
                    return pd.DataFrame({'date': dates, 'value': [2.5, 2.5]})
                if series_id == "DTWEXBGS":
                    return pd.DataFrame({'date': dates, 'value': [100.0, 100.0]})
                return pd.DataFrame({'date': dates, 'value': [1.0, 1.0]})
            
            mock_fetch.side_effect = side_effect
            snapshot = self.provider.get_snapshot()
            self.assertEqual(snapshot.regime, "RISK_OFF")
            self.assertIn("VIX cao → risk-off toàn cầu, tránh midcap/penny VN", snapshot.notes)

            # RISK_ON: vix < 15 and curve > 0.5 and dxy_pct < -1
            def side_effect_on(series_id):
                dates = [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-02-01')]
                if series_id == "VIXCLS":
                    return pd.DataFrame({'date': dates, 'value': [15.0, 10.0]})
                if series_id == "DGS10":
                    return pd.DataFrame({'date': dates, 'value': [4.0, 4.0]})
                if series_id == "DGS2":
                    return pd.DataFrame({'date': dates, 'value': [3.0, 3.0]})
                if series_id == "DTWEXBGS":
                    return pd.DataFrame({'date': dates, 'value': [105.0, 100.0]})
                return pd.DataFrame({'date': dates, 'value': [1.0, 1.0]})
            
            mock_fetch.side_effect = side_effect_on
            snapshot = self.provider.get_snapshot()
            self.assertEqual(snapshot.regime, "RISK_ON")

if __name__ == '__main__':
    unittest.main()
