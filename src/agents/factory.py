import os
from typing import Any
from src.core.analyzer import Analyzer
from src.agents.pipeline import AgentPipeline

class MultiAgentAdapter:
    """
    Adapter to wrap AgentPipeline so it exposes the same `analyze(symbol)` 
    interface as the legacy `Analyzer`.
    """
    def __init__(self):
        self.pipeline = AgentPipeline()

    def analyze(self, symbol: str) -> dict:
        try:
            opinion, context = self.pipeline.run(symbol)
            
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
                "is_multi_agent": True
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
    def create(use_agents: bool = False) -> Any:
        """
        Creates and returns an analyzer object.
        
        Args:
            use_agents: If True, uses the new Multi-Agent pipeline via an adapter.
                        If False, falls back to the legacy Analyzer unless 
                        AGENT_ARCH="multi" is set in the environment.
        """
        if not use_agents:
            env_arch = os.environ.get("AGENT_ARCH", "").lower()
            if env_arch == "multi":
                use_agents = True

        if use_agents:
            return MultiAgentAdapter()
        else:
            return Analyzer()
