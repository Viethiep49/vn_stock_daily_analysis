import os
from typing import Any
from src.core.analyzer import Analyzer
from src.agents.pipeline import AgentPipeline

class MultiAgentAdapter:
    """
    Adapter to wrap AgentPipeline so it exposes the same `analyze(symbol)` 
    interface as the legacy `Analyzer`.
    """
    def __init__(self, skill: str = None):
        self.pipeline = AgentPipeline()
        self.skill = skill

    def analyze(self, symbol: str, skill: str = None) -> dict:
        try:
            # Use the skill provided at analyze time, or fallback to the one from init
            effective_skill = skill or self.skill
            opinion, context = self.pipeline.run(symbol, skill_name=effective_skill)
            
            # Format the output to be compatible with both main.py and app.py
            llm_analysis = f"### Final Signal: {opinion.signal}\n**Confidence: {opinion.confidence:.2f}**\n\n{opinion.reasoning}"
            
            if context.opinions:
                llm_analysis += "\n\n---\n### Detailed Agent Opinions"
                for agent_name, agent_opinion in context.opinions.items():
                    llm_analysis += f"\n\n**{agent_name.capitalize()} Agent:**\n- Signal: {agent_opinion.signal}\n- Reasoning: {agent_opinion.reasoning}"

            return {
                "symbol": symbol,
                "status": "success",
                "info": context.data.get("stock_info", {}),
                "quote": context.data.get("realtime_quote", {}),
                "circuit_breaker": context.data.get("circuit_breaker", {}), 
                "tech_summary": "Phân tích bởi Multi-Agent System (Technical + Risk + Decision Agents)",
                "llm_analysis": llm_analysis,
                "is_multi_agent": True,
                "opinion": {
                    "signal": opinion.signal,
                    "confidence": opinion.confidence,
                    "sentiment_score": opinion.sentiment_score,
                    "operation_advice": opinion.operation_advice,
                    "key_points": opinion.key_points,
                    "reasoning": opinion.reasoning,
                    "key_levels": opinion.key_levels
                }
            }
        except Exception as e:
            import traceback
            return {
                "symbol": symbol,
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

class AnalyzerFactory:
    @staticmethod
    def create(use_agents: bool = False, skill: str = None) -> Any:
        """
        Creates and returns an analyzer object.
        
        Args:
            use_agents: If True, uses the new Multi-Agent pipeline via an adapter.
                        If False, falls back to the legacy Analyzer unless 
                        AGENT_ARCH="multi" is set in the environment.
            skill: Optional skill/strategy name to use in multi-agent mode.
        """
        if not use_agents:
            env_arch = os.environ.get("AGENT_ARCH", "").lower()
            if env_arch == "multi":
                use_agents = True

        if use_agents:
            return MultiAgentAdapter(skill=skill)
        else:
            return Analyzer()
