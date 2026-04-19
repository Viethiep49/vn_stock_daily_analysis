import logging
from typing import Optional
from src.core.llm_client import LiteLLMClient
from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext

logger = logging.getLogger(__name__)

class IntelAgent(BaseAgent):
    """
    Market Intelligence Expert agent.
    Gathers news, assesses sentiment, and identifies catalysts or risks.
    """
    
    def __init__(self, llm_client: Optional[LiteLLMClient] = None, registry=None):
        super().__init__(llm_client, registry)

    def system_prompt(self, context: AgentContext) -> str:
        history = context.metadata.get('history', [])
        history_instruction = ""
        if history:
            history_summary = "\n".join([f"- {h['timestamp']}: {h['signal']} at {h['price']}" for h in history])
            history_instruction = f"\nRecent analysis history for {context.symbol}:\n{history_summary}\nCheck if recent news confirms or contradicts past analysis."

        return (
            "You are a Market Intelligence Expert. You gather news, assess sentiment, and identify catalysts or risks. "
            "Use `get_stock_news_tool` to fetch recent news. "
            f"{history_instruction}"
            "\nYour goal is to determine if the news is positive (BUY), negative (SELL), or neutral (HOLD). "
            "Provide your final answer as a JSON block matching the AgentOpinion schema:\n"
            "{\n"
            '  "signal": "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "reasoning": "detailed explanation"\n'
            "}"
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Please analyze the latest news and market intelligence for {context.symbol}."
