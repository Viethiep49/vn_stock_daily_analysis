from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

class TechnicalAgent(BaseAgent):
    """
    Focuses on technical analysis using trends, MA crossover, RSI, and volume patterns.
    """
    
    def system_prompt(self, context: AgentContext) -> str:
        tech_score = context.data.get('scores', {}).get('technical')
        score_instruction = f"Objective Technical Score Data: {tech_score}. Incorporate this objective score into your analysis. " if tech_score else ""
        
        history = context.metadata.get('history', [])
        history_instruction = ""
        if history:
            history_summary = "\n".join([f"- {h['timestamp']}: {h['signal']} at {h['price']}" for h in history])
            history_instruction = f"Recent analysis history for {context.symbol}:\n{history_summary}\nConsider past signals for consistency or to identify potential mistakes."

        return (
            "You are a Technical Analysis Expert. Focus on trends, MA crossover, RSI, and volume patterns. "
            f"{score_instruction}"
            f"{history_instruction}"
            "Use the provided tools to gather historical data and current quotes to perform your analysis. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Analyze the technical signals for symbol: {context.symbol}."
