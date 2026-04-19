from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

class TechnicalAgent(BaseAgent):
    """
    Focuses on technical analysis using trends, MA crossover, RSI, and volume patterns.
    """
    
    def system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a Technical Analysis Expert. Focus on trends, MA crossover, RSI, and volume patterns. "
            "Use the provided tools to gather historical data and current quotes to perform your analysis. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Analyze the technical signals for symbol: {context.symbol}."
