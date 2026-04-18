"""AI Explainer: Translates hard scores into human-readable narratives."""
import logging
from typing import Optional
from src.core.llm_client import LiteLLMClient
from src.scoring.aggregator import AnalysisReport

logger = logging.getLogger(__name__)


class LLMExplainer:
    def __init__(self, llm_client: Optional[LiteLLMClient] = None):
        self.llm = llm_client or LiteLLMClient()

    def explain(self, report: AnalysisReport) -> str:
        """Construct prompt from ScoreCards and generate narrative."""
        # 1. Prepare data summary
        cards_text = ""
        for c in report.cards:
            cards_text += f"- {c.strategy_name}: {c.signal.value} (Score: {c.score}). Reason: {c.reason}\n"

        # 2. Build prompt
        prompt = f"""
You are a senior stock analyst at a top Vietnamese investment firm.
You have a technical scoring report for the symbol: {report.symbol or 'Stock'}.

Overall Score: {report.composite:.1f}/100
Final Recommendation: {report.final_signal.value}

Breakdown by Strategies:
{cards_text}

Market Data Summary:
Price: {report.quote.get('price') if report.quote else 'N/A'} (Change: {report.quote.get('change_pct') if report.quote else 'N/A'}%)
Risk Warning: {report.circuit_breaker.get('warning') if report.circuit_breaker else 'None'}

Please provide a concise but professional narrative analysis in Vietnamese (approx 200 words).
Structure it into 3 parts:
1. Technical Trend Summary (summarize the strategies).
2. Risk vs Reward assessment.
3. Actionable Conclusion (Buy/Hold/Sell) and conviction level.

Constraint: DO NOT change the scores or the final signal. Your job is to EXPLAIN the existing math fairly.
"""
        logger.info(f"Generating narrative for {report.symbol}...")
        try:
            narrative = self.llm.generate(prompt)
            return narrative
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "Unable to generate AI narrative at this time."
