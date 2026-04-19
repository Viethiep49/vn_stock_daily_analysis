import pytest
from unittest.mock import MagicMock
from src.agents.technical_agent import TechnicalAgent
from src.agents.risk_agent import RiskAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.protocols import AgentContext, AgentOpinion, Signal

@pytest.fixture
def mock_llm_client():
    return MagicMock()

def test_technical_agent_prompts(mock_llm_client):
    agent = TechnicalAgent(llm_client=mock_llm_client)
    context = AgentContext(symbol="TCB")
    
    system_prompt = agent.system_prompt(context)
    user_prompt = agent.user_prompt(context)
    
    assert "Technical Analysis Expert" in system_prompt
    assert "TCB" in user_prompt

def test_risk_agent_prompts(mock_llm_client):
    agent = RiskAgent(llm_client=mock_llm_client)
    context = AgentContext(symbol="TCB")
    
    system_prompt = agent.system_prompt(context)
    user_prompt = agent.user_prompt(context)
    
    assert "Risk Management Expert" in system_prompt
    assert "TCB" in user_prompt

def test_decision_agent_prompts(mock_llm_client):
    agent = DecisionAgent(llm_client=mock_llm_client)
    technical_opinion = AgentOpinion(signal=Signal.BUY, confidence=0.8, reasoning="MA Crossover")
    risk_opinion = AgentOpinion(signal=Signal.HOLD, confidence=0.9, reasoning="No major risks")
    
    context = AgentContext(
        symbol="TCB",
        opinions={
            "TechnicalAgent": technical_opinion,
            "RiskAgent": risk_opinion
        }
    )
    
    system_prompt = agent.system_prompt(context)
    user_prompt = agent.user_prompt(context)
    
    assert "Lead Investment Decision Agent" in system_prompt
    assert "TechnicalAgent" in user_prompt
    assert "BUY" in user_prompt
    assert "RiskAgent" in user_prompt
    assert "HOLD" in user_prompt

def test_decision_agent_no_tools(mock_llm_client):
    agent = DecisionAgent(llm_client=mock_llm_client)
    assert len(agent.registry.get_schemas()) == 0
