"""
tests/test_data_provider.py — Unit tests cho VNStockProvider (gọi API thật KBS)

LƯU Ý: Một số tests gọi API thực, cần kết nối internet.
        Dùng pytest marker @pytest.mark.integration để bỏ qua khi offline.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.data_provider.vnstock_provider import VNStockProvider
from src.data_provider.fallback_router import FallbackRouter


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def provider():
    return VNStockProvider()


@pytest.fixture
def mock_provider():
    """Provider với Vnstock client bị mock — không gọi API"""
    p = VNStockProvider()
    mock_client = MagicMock()

    # Mock company.overview()
    mock_client.company.overview.return_value = pd.DataFrame([{
        'exchange': 'HOSE', 'company_type': 'Công ty cổ phần',
        'website': 'https://example.com', 'address': 'TP.HCM',
        'number_of_employees': 5000, 'outstanding_shares': 1_000_000,
        'industry': '', 'tax_id': '0300000000'
    }])

    # Mock listing.symbols_by_exchange()
    mock_client.listing.symbols_by_exchange.return_value = pd.DataFrame([
        {'symbol': 'VNM', 'organ_name': 'CTCP Sữa Việt Nam', 'exchange': 'HOSE', 'type': 'stock', 'id': 1}
    ])

    # Mock quote.history()
    mock_client.quote.history.return_value = pd.DataFrame([
        {'time': '2026-04-15', 'open': 61.0, 'high': 62.0, 'low': 60.5, 'close': 61.1, 'volume': 2_000_000},
        {'time': '2026-04-16', 'open': 61.1, 'high': 62.5, 'low': 61.0, 'close': 61.3, 'volume': 3_115_500},
    ])

    p._client_cache['VNM'] = mock_client
    return p


# ────────────────────────────────────────────────────────────────────────────
# Tests: _clean_symbol
# ────────────────────────────────────────────────────────────────────────────

class TestCleanSymbol:
    def test_removes_exchange_suffix(self, provider):
        assert provider._clean_symbol("VNM.HO") == "VNM"

    def test_uppercase_output(self, provider):
        assert provider._clean_symbol("vnm.ho") == "VNM"

    def test_no_suffix(self, provider):
        assert provider._clean_symbol("FPT") == "FPT"

    def test_hnx_suffix(self, provider):
        assert provider._clean_symbol("ACB.HN") == "ACB"


# ────────────────────────────────────────────────────────────────────────────
# Tests: get_stock_info (với mock)
# ────────────────────────────────────────────────────────────────────────────

class TestGetStockInfo:
    def test_returns_dict(self, mock_provider):
        info = mock_provider.get_stock_info("VNM.HO")
        assert isinstance(info, dict)

    def test_has_required_keys(self, mock_provider):
        info = mock_provider.get_stock_info("VNM")
        for key in ['symbol', 'exchange', 'company_name']:
            assert key in info, f"Missing key: {key}"

    def test_symbol_is_cleaned(self, mock_provider):
        info = mock_provider.get_stock_info("VNM.HO")
        assert info['symbol'] == "VNM"

    def test_company_name_from_listing(self, mock_provider):
        info = mock_provider.get_stock_info("VNM")
        assert info['company_name'] == "CTCP Sữa Việt Nam"

    def test_exchange_correct(self, mock_provider):
        info = mock_provider.get_stock_info("VNM")
        assert info['exchange'] == "HOSE"

    def test_fallback_on_api_error(self, provider):
        """Khi API lỗi, phải trả về dict không lỗi (graceful fallback)"""
        with patch.object(provider, '_get_client', side_effect=RuntimeError("API down")):
            info = provider.get_stock_info("VNM")
        assert isinstance(info, dict)
        assert 'symbol' in info
        assert info.get('source') == 'fallback'


# ────────────────────────────────────────────────────────────────────────────
# Tests: get_historical_data (với mock)
# ────────────────────────────────────────────────────────────────────────────

class TestGetHistoricalData:
    def test_returns_dataframe(self, mock_provider):
        df = mock_provider.get_historical_data("VNM", "2026-04-15", "2026-04-16")
        assert isinstance(df, pd.DataFrame)

    def test_not_empty(self, mock_provider):
        df = mock_provider.get_historical_data("VNM", "2026-04-15", "2026-04-16")
        assert not df.empty

    def test_has_ohlcv_columns(self, mock_provider):
        df = mock_provider.get_historical_data("VNM", "2026-04-15", "2026-04-16")
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in df.columns, f"Missing column: {col}"

    def test_sorted_by_date(self, mock_provider):
        df = mock_provider.get_historical_data("VNM", "2026-04-15", "2026-04-16")
        dates = df['date'].tolist()
        assert dates == sorted(dates)

    def test_empty_dataframe_on_api_error(self, provider):
        """Khi API lỗi, phải trả về DataFrame rỗng"""
        with patch.object(provider, '_get_client', side_effect=RuntimeError("API down")):
            df = provider.get_historical_data("VNM", "2026-01-01", "2026-01-10")
        assert isinstance(df, pd.DataFrame)
        assert df.empty


# ────────────────────────────────────────────────────────────────────────────
# Tests: get_realtime_quote (với mock)
# ────────────────────────────────────────────────────────────────────────────

class TestGetRealtimeQuote:
    def test_returns_dict(self, mock_provider):
        quote = mock_provider.get_realtime_quote("VNM")
        assert isinstance(quote, dict)

    def test_has_required_keys(self, mock_provider):
        quote = mock_provider.get_realtime_quote("VNM")
        for key in ['symbol', 'price', 'change', 'volume']:
            assert key in quote, f"Missing key: {key}"

    def test_price_is_positive(self, mock_provider):
        quote = mock_provider.get_realtime_quote("VNM")
        assert quote['price'] > 0

    def test_price_reflects_latest_close(self, mock_provider):
        """Giá phải là close của ngày cuối cùng trong mock data"""
        quote = mock_provider.get_realtime_quote("VNM")
        assert quote['price'] == pytest.approx(61.3, abs=0.1)

    def test_change_calculated_correctly(self, mock_provider):
        """change = close_hôm_nay - close_hôm_qua = 61.3 - 61.1 = 0.2"""
        quote = mock_provider.get_realtime_quote("VNM")
        assert quote['change'] == pytest.approx(0.2, abs=0.05)

    def test_volume_is_int(self, mock_provider):
        quote = mock_provider.get_realtime_quote("VNM")
        assert isinstance(quote['volume'], int)

    def test_fallback_on_error(self, provider):
        with patch.object(provider, '_get_client', side_effect=RuntimeError("API down")):
            quote = provider.get_realtime_quote("VNM")
        assert isinstance(quote, dict)
        assert quote.get('price') == 0


# ────────────────────────────────────────────────────────────────────────────
# Tests: FallbackRouter
# ────────────────────────────────────────────────────────────────────────────

class TestFallbackRouter:
    def test_execute_with_single_provider(self):
        p = MagicMock()
        p.get_stock_info.return_value = {"symbol": "VNM"}
        router = FallbackRouter([p])
        result = router.execute_with_fallback("get_stock_info", "VNM")
        assert result['symbol'] == "VNM"

    def test_fallback_to_second_on_first_failure(self):
        p1 = MagicMock()
        p1.get_stock_info.side_effect = RuntimeError("First provider failed")
        p2 = MagicMock()
        p2.get_stock_info.return_value = {"symbol": "VNM", "source": "backup"}

        router = FallbackRouter([p1, p2])
        result = router.execute_with_fallback("get_stock_info", "VNM")
        assert result['source'] == "backup"

    def test_raises_when_all_providers_fail(self):
        p1 = MagicMock()
        p1.get_stock_info.side_effect = RuntimeError("Error")
        router = FallbackRouter([p1])
        with pytest.raises(Exception):
            router.execute_with_fallback("get_stock_info", "VNM")


# ────────────────────────────────────────────────────────────────────────────
# Integration tests (gọi API thật — cần internet)
# Chạy riêng: pytest tests/test_data_provider.py -m integration
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.integration
class TestRealAPIIntegration:
    """Tests gọi API thật — cần kết nối internet"""

    def test_real_stock_info_vnm(self):
        p = VNStockProvider()
        info = p.get_stock_info("VNM.HO")
        assert info['symbol'] == "VNM"
        assert "Vinamilk" in info.get('company_name', '') or "Sữa" in info.get('company_name', '')
        assert info['exchange'] == "HOSE"

    def test_real_historical_data_5_days(self):
        p = VNStockProvider()
        today = datetime.today().strftime('%Y-%m-%d')
        week_ago = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        df = p.get_historical_data("VNM", week_ago, today)
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert 'close' in df.columns

    def test_real_quote_price_reasonable(self):
        """VNM phải có giá hợp lý (20-200 nghìn đồng, tức 20-200 đơn vị KBS)"""
        p = VNStockProvider()
        quote = p.get_realtime_quote("VNM")
        assert 20 <= quote['price'] <= 200, f"Giá bất thường: {quote['price']}"
