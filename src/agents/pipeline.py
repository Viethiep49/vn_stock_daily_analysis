from typing import Tuple
from src.agents.protocols import AgentContext, AgentOpinion, Signal
from src.agents.technical_agent import TechnicalAgent
from src.agents.risk_agent import RiskAgent
from src.agents.decision_agent import DecisionAgent
from src.data_provider.vnstock_provider import VNStockProvider
from src.core.llm_client import LiteLLMClient
import logging

logger = logging.getLogger(__name__)

class AgentPipeline:
    """
    Orchestrates the multi-agent analysis flow:
    TechnicalAgent -> RiskAgent -> DecisionAgent.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client or LiteLLMClient()
        self.data_provider = VNStockProvider()
        self.technical_agent = TechnicalAgent(llm_client=self.llm_client)
        self.risk_agent = RiskAgent(llm_client=self.llm_client)
        self.decision_agent = DecisionAgent(llm_client=self.llm_client)

    def _apply_risk_override(self, context: AgentContext, final_opinion: AgentOpinion) -> AgentOpinion:
        risk_flags = context.risk_flags
        risk_opinion = context.opinions.get("risk")
        
        extreme_risk = False
        if risk_opinion and risk_opinion.signal in [Signal.SELL, Signal.STRONG_SELL]:
            extreme_risk = True
            
        if any(flag in risk_flags for flag in ["Ceiling/Floor Hit", "Extreme Volatility"]):
            extreme_risk = True
                
        if extreme_risk:
            downgrade_map = {
                Signal.STRONG_BUY: Signal.BUY,
                Signal.BUY: Signal.HOLD,
                Signal.HOLD: Signal.SELL,
                Signal.SELL: Signal.STRONG_SELL,
                Signal.STRONG_SELL: Signal.STRONG_SELL
            }
            original_signal = final_opinion.signal
            new_signal = downgrade_map.get(original_signal, original_signal)
            
            # Since pydantic models can be mutated or we create a new one:
            # Let's just mutate the fields if allowed, or re-instantiate
            # In pydantic v1 or v2 we can modify fields. Assuming we can.
            if new_signal != original_signal:
                final_opinion.signal = new_signal
                if "[Risk Override Applied]" not in final_opinion.reasoning:
                    final_opinion.reasoning += " [Risk Override Applied]: Downgraded due to extreme risk."
                
        return final_opinion

    def run(self, symbol: str) -> Tuple[AgentOpinion, AgentContext]:
        """
        Run the full analysis pipeline for a given symbol.
        Returns a tuple of (final_opinion, context).
        """
        logger.info(f"Starting analysis pipeline for symbol: {symbol}")
        
        # 1. Initialize context and populate initial data
        context = AgentContext(symbol=symbol)
        
        try:
            # Populate basic stock info and current price
            context.data["stock_info"] = self.data_provider.get_stock_info(symbol)
            context.data["realtime_quote"] = self.data_provider.get_realtime_quote(symbol)
        except Exception as e:
            logger.error(f"Error pre-fetching data for {symbol}: {e}")

        # 2. Run Technical Analysis Agent
        logger.info(f"Running TechnicalAgent for {symbol}...")
        tech_opinion = None
        try:
            tech_opinion = self.technical_agent.run(context)
            context.opinions["technical"] = tech_opinion
        except Exception as e:
            logger.error(f"TechnicalAgent failed for {symbol}: {e}")

        # 3. Run Risk Management Agent
        logger.info(f"Running RiskAgent for {symbol}...")
        try:
            risk_opinion = self.risk_agent.run(context)
            context.opinions["risk"] = risk_opinion
        except Exception as e:
            logger.error(f"RiskAgent failed for {symbol}: {e}")

        # 4. Run Decision Making Agent (Final Synthesis)
        logger.info(f"Running DecisionAgent for {symbol}...")
        final_decision = None
        try:
            final_decision = self.decision_agent.run(context)
        except Exception as e:
            logger.error(f"DecisionAgent failed for {symbol}: {e}")
            
        # Fallback logic
        if not final_decision:
            if tech_opinion:
                final_decision = tech_opinion
            else:
                final_decision = AgentOpinion(
                    signal=Signal.HOLD,
                    confidence=0.5,
                    reasoning="Fallback: All agents failed, defaulting to HOLD."
                )

        # Apply Risk Override
        final_decision = self._apply_risk_override(context, final_decision)
        
        logger.info(f"Pipeline completed for {symbol}. Final signal: {final_decision.signal}")
        return final_decision, context
