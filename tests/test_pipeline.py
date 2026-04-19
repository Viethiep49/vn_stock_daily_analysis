import pytest
from unittest.mock import MagicMock, patch
from src.agents.pipeline import AgentPipeline
from src.agents.protocols import AgentOpinion, Signal, AgentContext

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def pipeline(mock_llm_client):
    return AgentPipeline(llm_client=mock_llm_client)

def test_pipeline_run_success(pipeline, mock_llm_client):
    # Mock stock info and quote
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        
        mock_info.return_value = {"symbol": "VNM", "company_name": "Vinamilk"}
        mock_quote.return_value = {"price": 70000, "change": 500}
        
        # Mock agents' run methods to avoid actual LLM calls
        pipeline.technical_agent.run = MagicMock(return_value=AgentOpinion(
            signal=Signal.BUY, confidence=0.8, reasoning="Strong technicals"
        ))
        pipeline.risk_agent.run = MagicMock(return_value=AgentOpinion(
            signal=Signal.HOLD, confidence=0.9, reasoning="Low risk"
        ))
        pipeline.decision_agent.run = MagicMock(return_value=AgentOpinion(
            signal=Signal.BUY, confidence=0.85, reasoning="Final decision: BUY"
        ))
        
        result, context = pipeline.run("VNM")
        
        assert isinstance(result, AgentOpinion)
        assert result.signal == Signal.BUY
        assert result.confidence == 0.85
        assert "Final decision: BUY" in result.reasoning
        
        mock_info.assert_called_once_with("VNM")
        mock_quote.assert_called_once_with("VNM")
        pipeline.technical_agent.run.assert_called_once()
        pipeline.risk_agent.run.assert_called_once()
        pipeline.decision_agent.run.assert_called_once()

def test_pipeline_populates_context(pipeline, mock_llm_client):
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        
        mock_info.return_value = {"symbol": "VNM", "company_name": "Vinamilk"}
        mock_quote.return_value = {"price": 70000}
        
        # To check context, we wrap the run methods but still call them or mock them
        captured_contexts = []
        def side_effect(context):
            captured_contexts.append(context)
            return AgentOpinion(signal=Signal.HOLD, confidence=0.5, reasoning="mock")
            
        pipeline.technical_agent.run = MagicMock(side_effect=side_effect)
        pipeline.risk_agent.run = MagicMock(side_effect=side_effect)
        pipeline.decision_agent.run = MagicMock(side_effect=side_effect)
        
        pipeline.run("VNM")
        
        assert len(captured_contexts) == 3
        for context in captured_contexts:
            assert context.symbol == "VNM"
            assert context.data["stock_info"] == {"symbol": "VNM", "company_name": "Vinamilk"}
            assert context.data["realtime_quote"] == {"price": 70000}

def test_pipeline_risk_override_downgrades_signal(pipeline, mock_llm_client):
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        mock_info.return_value = {}
        mock_quote.return_value = {}
        
        pipeline.technical_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.BUY, confidence=0.8, reasoning="Tech"))
        pipeline.risk_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.SELL, confidence=0.9, reasoning="Risk high"))
        pipeline.decision_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.STRONG_BUY, confidence=0.9, reasoning="Final Decision"))
        
        result, context = pipeline.run("VNM")
        assert result.signal == Signal.BUY
        assert "[Risk Override Applied]: Downgraded due to extreme risk." in result.reasoning

def test_pipeline_risk_override_flags(pipeline, mock_llm_client):
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        mock_info.return_value = {}
        mock_quote.return_value = {}
        
        pipeline.technical_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.BUY, confidence=0.8, reasoning="Tech"))
        def set_risk_flags(context):
            context.risk_flags.append("Extreme Volatility")
            return AgentOpinion(signal=Signal.HOLD, confidence=0.9, reasoning="Risk neutral")
        pipeline.risk_agent.run = MagicMock(side_effect=set_risk_flags)
        pipeline.decision_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.BUY, confidence=0.9, reasoning="Final Decision"))
        
        result, context = pipeline.run("VNM")
        assert result.signal == Signal.HOLD
        assert "[Risk Override Applied]: Downgraded due to extreme risk." in result.reasoning

def test_pipeline_fallback_when_decision_agent_fails(pipeline, mock_llm_client):
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        mock_info.return_value = {}
        mock_quote.return_value = {}
        
        pipeline.technical_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.BUY, confidence=0.8, reasoning="Tech"))
        pipeline.risk_agent.run = MagicMock(return_value=AgentOpinion(signal=Signal.HOLD, confidence=0.9, reasoning="Risk"))
        
        # Simulate decision agent failing by raising Exception
        pipeline.decision_agent.run = MagicMock(side_effect=Exception("LLM Timeout"))
        
        result, context = pipeline.run("VNM")
        assert result.signal == Signal.BUY
        assert result.reasoning == "Tech"

def test_pipeline_fallback_when_all_fail(pipeline, mock_llm_client):
    with patch('src.data_provider.vnstock_provider.VNStockProvider.get_stock_info') as mock_info, \
         patch('src.data_provider.vnstock_provider.VNStockProvider.get_realtime_quote') as mock_quote:
        mock_info.return_value = {}
        mock_quote.return_value = {}
        
        pipeline.technical_agent.run = MagicMock(side_effect=Exception("Tech Error"))
        pipeline.risk_agent.run = MagicMock(side_effect=Exception("Risk Error"))
        pipeline.decision_agent.run = MagicMock(side_effect=Exception("LLM Timeout"))
        
        result, context = pipeline.run("VNM")
        assert result.signal == Signal.HOLD
        assert "Fallback" in result.reasoning
