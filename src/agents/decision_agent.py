from typing import List, Dict, Any, Optional
from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext, AgentOpinion
from src.agents.tools.registry import ToolRegistry

class DecisionAgent(BaseAgent):
    """
    Synthesizes results from Technical and Risk agents into a final recommendation.
    Does NOT use tools.
    """
    
    def __init__(self, llm_client=None):
        # Pass an empty registry to ensure no tools are used
        super().__init__(llm_client=llm_client, registry=ToolRegistry())

    def system_prompt(self, context: AgentContext) -> str:
        return (
            "You are the Lead Investment Decision Agent. "
            "Synthesize opinions from Technical, Risk, and Market Intelligence (Intel) agents into a final recommendation. "
            "Your output must be a JSON block containing 'signal', 'confidence', 'reasoning', and 'key_levels'."
        )

    def user_prompt(self, context: AgentContext) -> str:
        opinions_summary = ""
        for name, opinion in context.opinions.items():
            opinions_summary += f"\nAgent: {name}\nSignal: {opinion.signal}\nConfidence: {opinion.confidence}\nReasoning: {opinion.reasoning}\n"
        
        return (
            f"Analyze the following opinions for symbol {context.symbol} and provide a final decision:\n"
            f"{opinions_summary}"
        )
