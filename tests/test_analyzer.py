"""
tests/test_analyzer.py — Integration tests cho Analyzer (core orchestrator)

Dùng mock hoàn toàn để không phụ thuộc API key LLM hay mạng.
"""
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from src.core.analyzer import Analyzer


# ────────────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_df():
    """DataFrame lịch sử 60 phiên giả lập (cần tối thiểu 50 cho IndicatorEngine)"""
    data = [
        {'date': f'2026-03-{i:02d}', 'open': 61.0, 'high': 61.0,
         'low': 61.0, 'close': 61.0, 'volume': 2_000_000}
        for i in range(1, 61)
    ]
    return pd.DataFrame(data)


@pytest.fixture
def mock_quote():
    return {
        "symbol": "VNM", "price": 61.3, "change": 0.2,
        "change_pct": 0.33, "volume": 3_115_500,
        "open": 61.1, "high": 62.5, "low": 61.0, "date": "2026-04-17"
    }


@pytest.fixture
def mock_info():
    return {
        "symbol": "VNM", "exchange": "HOSE",
        "company_name": "CTCP Sữa Việt Nam",
        "industry": "Thực phẩm", "website": "https://vinamilk.com.vn"
    }


@pytest.fixture
def analyzer_with_mocks(mock_df, mock_quote, mock_info):
    """Analyzer với data provider và LLM hoàn toàn bị mock"""
    with patch("src.scoring.strategy_runner.StrategyRunner.load_dir") as mock_load:
        # Prevent actually loading YAMLs during tests
        mock_load.return_value = MagicMock()
        analyzer = Analyzer()

    mock_router = MagicMock()
    mock_router.execute_with_fallback.side_effect = lambda method, *args: {
        "get_stock_info": mock_info,
        "get_realtime_quote": mock_quote,
        "get_historical_data": mock_df,
    }[method]

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "VNM có xu hướng tăng. Khuyến nghị GIỮ."

    from src.scoring.aggregator import ScoreCard
    from src.scoring.signals import Signal
    analyzer.strategy_runner.run.return_value = [
        ScoreCard("Test", 60, Signal.NEUTRAL, "test", 1.0, 0)
    ]

    analyzer.router = mock_router
    analyzer.llm = mock_llm
    # Wire up explainer with the mock llm
    analyzer.explainer.llm = mock_llm

    return analyzer


# ────────────────────────────────────────────────────────────────────────────
# Tests: Validation phase
# ────────────────────────────────────────────────────────────────────────────

class TestAnalyzerValidation:
    def test_invalid_symbol_returns_failed(self):
        analyzer = Analyzer.__new__(Analyzer)
        analyzer.router = MagicMock()
        analyzer.circuit_breaker = MagicMock()
        analyzer.llm = MagicMock()
        result = analyzer.analyze("INVALID@SYMBOL")
        assert result['status'] == 'failed'
        assert 'error' in result

    def test_empty_symbol_returns_failed(self):
        analyzer = Analyzer.__new__(Analyzer)
        analyzer.router = MagicMock()
        analyzer.circuit_breaker = MagicMock()
        analyzer.llm = MagicMock()
        result = analyzer.analyze("")
        assert result['status'] == 'failed'


# ────────────────────────────────────────────────────────────────────────────
# Tests: Successful analysis
# ────────────────────────────────────────────────────────────────────────────

class TestAnalyzerSuccess:
    def test_returns_success_status(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert result['status'] == 'success'

    def test_result_has_symbol(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'symbol' in result
        # Analyzer trả về normalized symbol (VNM.HO)
        assert "VNM" in result['symbol']

    def test_result_has_info(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'info' in result
        assert result['info']['company_name'] == "CTCP Sữa Việt Nam"

    def test_result_has_quote(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'quote' in result
        assert result['quote']['price'] > 0

    def test_result_has_llm_analysis(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'llm_analysis' in result
        assert len(result['llm_analysis']) > 0

    def test_result_has_report(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'report' in result
        assert result['report'].composite >= 0

    def test_result_has_indicators(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'indicators' in result
        assert result['indicators'].MA20 is not None

    def test_llm_generate_called_once(self, analyzer_with_mocks):
        analyzer_with_mocks.analyze("VNM.HO")
        analyzer_with_mocks.llm.generate.assert_called_once()

    def test_prompt_contains_symbol(self, analyzer_with_mocks):
        analyzer_with_mocks.analyze("VNM.HO")
        prompt = analyzer_with_mocks.llm.generate.call_args[0][0]
        assert "VNM" in prompt

    def test_prompt_contains_price(self, analyzer_with_mocks):
        analyzer_with_mocks.analyze("VNM.HO")
        prompt = analyzer_with_mocks.llm.generate.call_args[0][0]
        assert "61" in prompt  # price 61.3 phải có trong prompt


# ────────────────────────────────────────────────────────────────────────────
# Tests: Circuit breaker integration
# ────────────────────────────────────────────────────────────────────────────

class TestAnalyzerCircuitBreaker:
    def test_no_warning_for_normal_price(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        cb = result.get('circuit_breaker')
        # Giá 61.3 từ quote vs. prev_close 61.2 → không ở trần/sàn
        if cb:
            assert cb.get('warning') is None

    def test_circuit_breaker_key_in_result(self, analyzer_with_mocks):
        result = analyzer_with_mocks.analyze("VNM.HO")
        assert 'circuit_breaker' in result


# ────────────────────────────────────────────────────────────────────────────
# Tests: Error handling
# ────────────────────────────────────────────────────────────────────────────

class TestAnalyzerErrorHandling:
    def test_data_provider_error_returns_failed(self):
        analyzer = Analyzer.__new__(Analyzer)
        mock_router = MagicMock()
        mock_router.execute_with_fallback.side_effect = RuntimeError("Network error")
        analyzer.router = mock_router
        analyzer.circuit_breaker = MagicMock()
        analyzer.llm = MagicMock()

        result = analyzer.analyze("VNM.HO")
        assert result['status'] == 'failed'
        assert 'error' in result

    def test_llm_error_returns_failed(self, mock_df, mock_quote, mock_info):
        analyzer = Analyzer.__new__(Analyzer)

        mock_router = MagicMock()
        mock_router.execute_with_fallback.side_effect = lambda method, *args: {
            "get_stock_info": mock_info,
            "get_realtime_quote": mock_quote,
            "get_historical_data": mock_df,
        }[method]

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("LLM timeout")

        from src.market.circuit_breaker import CircuitBreakerHandler
        analyzer.router = mock_router
        analyzer.circuit_breaker = CircuitBreakerHandler()
        analyzer.llm = mock_llm

        result = analyzer.analyze("VNM.HO")
        assert result['status'] == 'failed'
