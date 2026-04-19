from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

class RiskAgent(BaseAgent):
    """
    Focuses on safety, ceiling/floor hits, extreme volatility, and fundamental red flags.
    """
    
    def system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a Risk Management Expert. Focus on ceiling/floor hits, extreme volatility, and fundamental red flags. "
            "Evaluate the risks associated with the given stock. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Evaluate the risk for symbol: {context.symbol}."
