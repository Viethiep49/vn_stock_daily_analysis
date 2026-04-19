from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

class RiskAgent(BaseAgent):
    """
    Focuses on safety, ceiling/floor hits, extreme volatility, and fundamental red flags.
    """
    
    def system_prompt(self, context: AgentContext) -> str:
        fund_score = context.data.get('scores', {}).get('fundamental')
        score_instruction = f"Fundamental Score Data: {fund_score}. Issue a warning if the F-Score is extremely low (e.g., < 3). " if fund_score else ""
        return (
            "You are a Risk Management Expert. Focus on ceiling/floor hits, extreme volatility, and fundamental red flags. "
            f"{score_instruction}"
            "Evaluate the risks associated with the given stock. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Evaluate the risk for symbol: {context.symbol}."
