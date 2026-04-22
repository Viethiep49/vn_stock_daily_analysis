from src.agents import Signal, AgentOpinion, AgentContext
import pydantic

def test_signal_enum():
    assert Signal.BUY == "BUY"
    assert Signal.STRONG_BUY == "STRONG_BUY"
    assert Signal.HOLD == "HOLD"
    assert Signal.SELL == "SELL"
    assert Signal.STRONG_SELL == "STRONG_SELL"

def test_agent_opinion_valid():
    opinion = AgentOpinion(
        signal=Signal.BUY,
        confidence=0.8,
        sentiment_score=75,
        operation_advice="Strong momentum, consider entering at support.",
        key_points=["Rising volume", "Bullish MACD"],
        reasoning="Bullish momentum",
        key_levels={"support": 100.0, "resistance": 120.0, "target": 150.0}
    )
    assert opinion.signal == Signal.BUY
    assert opinion.confidence == 0.8
    assert opinion.sentiment_score == 75
    assert opinion.operation_advice == "Strong momentum, consider entering at support."
    assert "Rising volume" in opinion.key_points
    assert opinion.key_levels["support"] == 100.0

def test_agent_opinion_invalid_confidence():
    try:
        AgentOpinion(
            signal=Signal.BUY,
            confidence=1.5,
            reasoning="Too confident"
        )
        assert False, "Should have raised ValidationError"
    except pydantic.ValidationError:
        pass

def test_agent_context():
    opinion = AgentOpinion(
        signal=Signal.BUY,
        confidence=0.8,
        reasoning="Bullish momentum"
    )
    context = AgentContext(
        symbol="VNM",
        data={"price": 70000},
        opinions={"technical_agent": opinion},
        risk_flags=["High volatility"]
    )
    assert context.symbol == "VNM"
    assert context.opinions["technical_agent"].signal == Signal.BUY
    assert "High volatility" in context.risk_flags

if __name__ == "__main__":
    # Run tests manually if executed as a script
    test_signal_enum()
    test_agent_opinion_valid()
    test_agent_opinion_invalid_confidence()
    test_agent_context()
    print("All protocol tests passed!")
