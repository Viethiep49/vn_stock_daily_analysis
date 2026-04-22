import pytest
from unittest.mock import MagicMock

from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext, Signal

class MockAgent(BaseAgent):
    def system_prompt(self, context: AgentContext) -> str:
        return "System prompt"
    
    def user_prompt(self, context: AgentContext) -> str:
        return f"Analyze {context.symbol}"

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def agent(mock_llm_client):
    return MockAgent(llm_client=mock_llm_client)

def test_base_agent_direct_response(agent, mock_llm_client):
    # Mock direct response without tool calls
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"signal": "BUY", "confidence": 0.8, "reasoning": "Looks good"}'
    mock_message.tool_calls = None
    mock_response.choices = [MagicMock(message=mock_message)]
    
    mock_llm_client.chat.return_value = mock_response
    
    context = AgentContext(symbol="VNM")
    opinion = agent.run(context)
    
    assert opinion.signal == Signal.BUY
    assert opinion.confidence == 0.8
    assert opinion.reasoning == "Looks good"
    assert mock_llm_client.chat.call_count == 1

def test_base_agent_tool_call_loop(agent, mock_llm_client):
    # 1. First call returns a tool call
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = "get_quote"
    tool_call.function.arguments = '{"symbol": "VNM"}'
    
    msg_1 = MagicMock()
    msg_1.content = None
    msg_1.tool_calls = [tool_call]
    msg_1.role = "assistant"
    
    resp_1 = MagicMock()
    resp_1.choices = [MagicMock(message=msg_1)]
    
    # 2. Second call returns final opinion
    msg_2 = MagicMock()
    msg_2.content = '{"signal": "HOLD", "confidence": 0.5, "reasoning": "Price is stable"}'
    msg_2.tool_calls = None
    msg_2.role = "assistant"
    
    resp_2 = MagicMock()
    resp_2.choices = [MagicMock(message=msg_2)]
    
    mock_llm_client.chat.side_effect = [resp_1, resp_2]
    
    # Mock registry
    agent.registry = MagicMock()
    agent.registry.execute.return_value = {"price": 100.0}
    agent.registry.get_schemas.return_value = []

    context = AgentContext(symbol="VNM")
    opinion = agent.run(context)
    
    assert opinion.signal == Signal.HOLD
    assert opinion.reasoning == "Price is stable"
    assert mock_llm_client.chat.call_count == 2
    agent.registry.execute.assert_called_once_with("get_quote", symbol="VNM")

if __name__ == "__main__":
    # Manually run tests if needed
    pass
