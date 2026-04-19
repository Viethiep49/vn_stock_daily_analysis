from typing import Tuple, Optional
from src.agents.protocols import AgentContext, AgentOpinion, Signal
from src.agents.technical_agent import TechnicalAgent
from src.agents.risk_agent import RiskAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.intel_agent import IntelAgent
from src.agents.skill_agent import SkillAgent
from src.agents.memory import AgentMemory
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
        self.memory = AgentMemory()
        self.technical_agent = TechnicalAgent(llm_client=self.llm_client)
        self.risk_agent = RiskAgent(llm_client=self.llm_client)
        self.decision_agent = DecisionAgent(llm_client=self.llm_client)
        self.intel_agent = IntelAgent(llm_client=self.llm_client)

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

    def run(self, symbol: str, skill_name: Optional[str] = None) -> Tuple[AgentOpinion, AgentContext]:
        """
        Run the full analysis pipeline for a given symbol.
        Returns a tuple of (final_opinion, context).
        """
        logger.info(f"Starting analysis pipeline for symbol: {symbol}")
        
        # 1. Initialize context and populate initial data
        context = AgentContext(symbol=symbol)
        context.data['scores'] = {}
        
        # Fetch historical memory
        history = self.memory.get_recent_history(symbol)
        context.metadata['history'] = history
        context.metadata['accuracy'] = self.memory.calculate_accuracy(symbol)
        
        try:
            # Populate basic stock info and current price
            context.data["stock_info"] = self.data_provider.get_stock_info(symbol)
            context.data["realtime_quote"] = self.data_provider.get_realtime_quote(symbol)
            
            # Fetch historical data for technical score
            from datetime import datetime, timedelta
            end_date = datetime.today().strftime('%Y-%m-%d')
            start_date = (datetime.today() - timedelta(days=100)).strftime('%Y-%m-%d')
            hist_df = self.data_provider.get_historical_data(symbol, start=start_date, end=end_date)
            
            if not hist_df.empty:
                from src.scoring.technical import calculate_technical_score
                context.data['scores']['technical'] = calculate_technical_score(hist_df)
            else:
                context.data['scores']['technical'] = None

            # Fetch financial data for fundamental score
            fin_report = self.data_provider.get_financial_report(symbol)
            if fin_report and 'data' in fin_report:
                import pandas as pd
                from src.scoring.fundamental import calculate_f_score
                fin_df = pd.DataFrame([fin_report['data']])
                context.data['scores']['fundamental'] = calculate_f_score(fin_df)
            else:
                context.data['scores']['fundamental'] = None

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

        # 4. Run Market Intelligence Agent
        logger.info(f"Running IntelAgent for {symbol}...")
        try:
            intel_opinion = self.intel_agent.run(context)
            context.opinions["intel"] = intel_opinion
        except Exception as e:
            logger.error(f"IntelAgent failed for {symbol}: {e}")

        # 5. Run Skill Agent (if requested)
        if skill_name:
            logger.info(f"Running SkillAgent for {symbol} with skill: {skill_name}...")
            try:
                skill_agent = SkillAgent(skill_name, llm_client=self.llm_client)
                skill_opinion = skill_agent.run(context)
                context.opinions["skill"] = skill_opinion
            except Exception as e:
                logger.error(f"SkillAgent failed for {symbol} ({skill_name}): {e}")

        # 6. Run Decision Making Agent (Final Synthesis)
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
        
        # Save to memory
        current_price = context.data.get("realtime_quote", {}).get("last_price", 0)
        self.memory.save_analysis(symbol, final_decision.signal, current_price, final_decision)
        
        logger.info(f"Pipeline completed for {symbol}. Final signal: {final_decision.signal}")
        return final_decision, context
