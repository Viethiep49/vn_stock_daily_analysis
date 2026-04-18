"""Smoke test for LLMExplainer prompt construction."""
from unittest.mock import MagicMock
from src.scoring.explainer import LLMExplainer
from src.scoring.aggregator import AnalysisReport, ScoreCard
from src.scoring.signals import Signal


def test_explainer_calls_llm_with_context():
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "AI Response"
    explainer = LLMExplainer(llm_client=mock_llm)

    report = AnalysisReport(
        composite=75.5,
        final_signal=Signal.BUY,
        cards=[
            ScoreCard("S1", 80, Signal.BUY, "Strong trend", 1.0, 0)
        ],
        symbol="FPT",
        quote={"price": 100000, "change_pct": 2.5},
        circuit_breaker={"warning": "None"}
    )

    res = explainer.explain(report)
    assert res == "AI Response"
    
    # Verify prompt contains key info
    prompt = mock_llm.generate.call_args[0][0]
    assert "FPT" in prompt
    assert "75.5/100" in prompt
    assert "Strong trend" in prompt
    assert "BUY" in prompt
