from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

class RiskAgent(BaseAgent):
    """
    Focuses on safety, ceiling/floor hits, extreme volatility, and fundamental red flags.
    """
    
    def system_prompt(self, context: AgentContext) -> str:
        fund_score = context.data.get('scores', {}).get('fundamental')
        score_instruction = f"Fundamental Score Data: {fund_score}. Issue a warning if the F-Score is extremely low (e.g., < 3). " if fund_score else ""
        
        history = context.metadata.get('history', [])
        history_instruction = ""
        if history:
            history_summary = "\n".join([f"- {h['timestamp']}: {h['signal']} at {h['price']}" for h in history])
            history_instruction = f"Recent analysis history for {context.symbol}:\n{history_summary}\nReview if previous risk assessments were accurate or if new risks are emerging."

        return (
            "You are a Risk Management Expert. Focus on ceiling/floor hits, extreme volatility, and fundamental red flags. "
            f"{score_instruction}"
            f"{history_instruction}"
            "Evaluate the risks associated with the given stock. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Evaluate the risk for symbol: {context.symbol}."
