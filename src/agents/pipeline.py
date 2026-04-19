from src.agents.protocols import AgentContext, AgentOpinion
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

    def run(self, symbol: str) -> AgentOpinion:
        """
        Run the full analysis pipeline for a given symbol.
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
        tech_opinion = self.technical_agent.run(context)
        context.opinions["technical"] = tech_opinion

        # 3. Run Risk Management Agent
        logger.info(f"Running RiskAgent for {symbol}...")
        risk_opinion = self.risk_agent.run(context)
        context.opinions["risk"] = risk_opinion

        # 4. Run Decision Making Agent (Final Synthesis)
        logger.info(f"Running DecisionAgent for {symbol}...")
        final_decision = self.decision_agent.run(context)
        
        logger.info(f"Pipeline completed for {symbol}. Final signal: {final_decision.signal}")
        return final_decision
