from src.agents.base_agent import BaseAgent
from src.agents.protocols import AgentContext
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
        history = context.metadata.get('history', [])
        accuracy = context.metadata.get('accuracy', {})
        
        history_instruction = ""
        if history:
            history_summary = "\n".join([f"- {h['timestamp']}: {h['signal']} at {h['price']}" for h in history])
            history_instruction = (
                f"\nRecent analysis history for {context.symbol}:\n{history_summary}\n"
                f"Historical Accuracy Calibration: {accuracy.get('historical_accuracy', 0.75) * 100:.1f}%\n"
                "Use this history to maintain strategic consistency and learn from past performance."
            )

        return (
            "You are the Lead Investment Decision Agent. "
            "Synthesize opinions from Technical, Risk, and Market Intelligence (Intel) agents into a final recommendation. "
            f"{history_instruction}"
            "\nYour output must be a JSON block containing the following fields:\n"
            "- 'signal': One of STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL\n"
            "- 'confidence': Float between 0 and 1\n"
            "- 'sentiment_score': Integer between 0 and 100\n"
            "- 'operation_advice': One sentence concise operation advice\n"
            "- 'key_points': A list of 3-5 key analysis points (strings)\n"
            "- 'reasoning': Detailed explanation of the decision\n"
            "- 'key_levels': Dictionary with 'support', 'resistance', 'target' levels"
        )

    def user_prompt(self, context: AgentContext) -> str:
        opinions_summary = ""
        for name, opinion in context.opinions.items():
            opinions_summary += f"\nAgent: {name}\nSignal: {opinion.signal}\nConfidence: {opinion.confidence}\nReasoning: {opinion.reasoning}\n"
        
        return (
            f"Analyze the following opinions for symbol {context.symbol} and provide a final decision:\n"
            f"{opinions_summary}"
        )
