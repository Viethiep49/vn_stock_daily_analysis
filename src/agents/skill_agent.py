import logging
from typing import Optional
from src.core.llm_client import LiteLLMClient
from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext
from src.agents.skills.registry import get_skill_content

logger = logging.getLogger(__name__)

class SkillAgent(BaseAgent):
    """
    An agent that specializes in a specific trading skill/strategy (e.g., VSA, CANSLIM).
    The strategy rules are loaded from a Markdown playbook.
    """
    
    def __init__(self, skill_name: str, llm_client: Optional[LiteLLMClient] = None, registry=None):
        super().__init__(llm_client, registry)
        self.skill_name = skill_name
        try:
            self.skill_content = get_skill_content(skill_name)
        except Exception as e:
            logger.error(f"Failed to load skill '{skill_name}': {e}")
            self.skill_content = f"Error loading skill '{skill_name}'."

    def system_prompt(self, context: AgentContext) -> str:
        valuation_info = ""
        if self.skill_name in ["BUFFETT", "GRAHAM", "LYNCH"]:
            # Inject DCF valuation if available (from Prompt 04)
            report = context.metadata.get('report')
            valuation = getattr(report, 'valuation', None) if report else context.metadata.get('valuation')
            
            if valuation:
                grade = getattr(valuation, 'grade', 'N/A')
                intrinsic = getattr(valuation, 'intrinsic_value_per_share', 0)
                upside = getattr(valuation, 'upside_pct', 0)
                notes = getattr(valuation, 'notes', [])
                notes_str = "; ".join(notes) if isinstance(notes, list) else str(notes)
                
                valuation_info = (
                    "### DCF VALUATION DATA ###\n"
                    f"Valuation Grade: {grade}\n"
                    f"Intrinsic Value: {intrinsic:,.0f} VND\n"
                    f"Upside: {upside:+.2f}%\n"
                    f"Notes: {notes_str}\n\n"
                )

        return (
            f"You are an expert financial analyst specializing in the {self.skill_name} methodology.\n\n"
            f"{valuation_info}"
            "### YOUR SPECIALIZED PLAYBOOK ###\n"
            f"{self.skill_content}\n\n"
            "### TASK ###\n"
            f"Analyze the stock {context.symbol} using the rules and principles above. "
            "Use any available tools to gather the necessary technical or fundamental data. "
            "Provide your final answer as a JSON block matching the AgentOpinion schema:\n"
            "{\n"
            '  "signal": "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL",\n'
            '  "confidence": 0.0 to 1.0,\n'
            '  "reasoning": "detailed explanation based on the skill rules"\n'
            "}"
        )

    def user_prompt(self, context: AgentContext) -> str:
        return f"Please perform a {self.skill_name} analysis for {context.symbol}."
