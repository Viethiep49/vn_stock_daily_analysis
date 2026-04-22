import pandas as pd
from unittest.mock import MagicMock
from src.screener.engine import ScreenerEngine, ScreenerConfig, ScreenerResult
from src.screener.filters import min_market_cap, rsi_in_range, composite_score_at_least
from src.scoring.indicators import IndicatorSet

def test_filter_primitives():
    # Test market cap filter
    row = {"market_cap_bn": 2000}
    assert min_market_cap(1000)(row) is True
    assert min_market_cap(3000)(row) is False
    assert min_market_cap(1000)({}) is False

    # Test RSI filter
    row = {"RSI14": 50}
    assert rsi_in_range(40, 60)(row) is True
    assert rsi_in_range(60, 80)(row) is False

    # Test composite score filter
    row = {"composite_score": 75}
    assert composite_score_at_least(70)(row) is True
    assert composite_score_at_least(80)(row) is False

def test_screener_engine_mock():
    # Setup mocks
    mock_provider = MagicMock()
    mock_provider.get_stock_info.return_value = {"symbol": "VNM", "industry": "Consumer"}
    mock_provider.get_realtime_quote.return_value = {"price": 70.5}
    mock_provider.get_historical_data.return_value = pd.DataFrame({
        "close": [70.5] * 30,
        "volume": [1000] * 30
    })

    # Create a real IndicatorSet because the engine uses .__dict__
    dummy_indicators = IndicatorSet(
        close=70.5, prev_close=70.0,
        MA5=70.0, MA10=70.0, MA20=70.0, MA50=70.0, MA200=70.0,
        prev_MA5=70.0, prev_MA20=70.0, prev_MA50=70.0,
        RSI14=55.0, prev_RSI14=54.0,
        MACD=0.1, MACD_signal=0.1, MACD_hist=0.0, prev_MACD_hist=0.0,
        BB_upper=72.0, BB_mid=70.0, BB_lower=68.0, ATR14=1.0,
        volume=1000.0, volume_ma20=1000.0, volume_ratio=1.0,
        support_20=65.0, resistance_20=75.0
    )

    mock_indicator = MagicMock()
    mock_indicator.compute.return_value = dummy_indicators

    mock_strategy = MagicMock()
    mock_strategy.run.return_value = [MagicMock(score=80, weight=1.0)]

    mock_aggregator = MagicMock()
    # Mock AnalysisReport because it also has fields used by the engine
    mock_report = MagicMock()
    mock_report.composite = 80.0
    mock_report.final_signal.value = "BUY"
    mock_aggregator.aggregate.return_value = mock_report

    # Initialize engine
    engine = ScreenerEngine(
        data_provider=mock_provider,
        indicator_engine=mock_indicator,
        strategy_runner=mock_strategy,
        aggregator=mock_aggregator
    )

    # Mock UniverseLoader to return 2 symbols
    with MagicMock() as mock_loader:
        mock_loader.load.return_value = [
            MagicMock(symbol="VNM", exchange="HOSE"),
            MagicMock(symbol="FPT", exchange="HOSE")
        ]
        engine.universe_loader = mock_loader

        # Run screener
        config = ScreenerConfig(
            filters=[composite_score_at_least(70)],
            top_n=5
        )
        result = engine.run(config)

        assert isinstance(result, ScreenerResult)
        assert len(result.selected) == 2
        assert result.coverage == 1.0
        symbols = set(result.selected["symbol"])
        assert "VNM" in symbols
        assert "FPT" in symbols
        assert result.selected.iloc[0]["composite_score"] == 80

def test_screener_filtering_logic():
    # Test that filters actually reduce the result set
    df = pd.DataFrame([
        {"symbol": "A", "composite_score": 90, "market_cap_bn": 5000},
        {"symbol": "B", "composite_score": 60, "market_cap_bn": 5000},
        {"symbol": "C", "composite_score": 90, "market_cap_bn": 500},
    ])
    
    # Simulate the filtering step in engine.py
    filters = [composite_score_at_least(80), min_market_cap(1000)]
    mask = pd.Series([True] * len(df))
    for f in filters:
        mask &= df.apply(f, axis=1)
    
    filtered_df = df[mask]
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["symbol"] == "A"
