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
            
            # Format a professional report
            signal_color = {
                "STRONG_BUY": "🟢 STRONG BUY",
                "BUY": "✅ BUY",
                "HOLD": "🟡 HOLD",
                "SELL": "❌ SELL",
                "STRONG_SELL": "🔴 STRONG SELL"
            }.get(opinion.signal.value if hasattr(opinion.signal, 'value') else str(opinion.signal), str(opinion.signal))

            report = [
                f"# Báo Cáo Phân Tích AI: {symbol}",
                f"## Tín Hiệu: {signal_color}",
                f"**Độ Tin Cậy:** {opinion.confidence * 100:.1f}% | **Điểm Tâm Lý:** {opinion.sentiment_score}/100",
                "",
                "### 🎯 Khuyến Nghị Vận Hành",
                f"> {opinion.operation_advice}",
                "",
                "### 📝 Phân Tích Chi Tiết",
                opinion.reasoning if not opinion.reasoning.strip().startswith('{') else "Cơ sở phân tích dựa trên sự tổng hợp từ các chuyên gia kỹ thuật và quản trị rủi ro.",
                "",
                "### 📊 Các Ngưỡng Quan Trọng",
            ]

            kl = opinion.key_levels
            if isinstance(kl, dict):
                res = kl.get('resistance', kl.get('resistance_1', 'N/A'))
                sup = kl.get('support', kl.get('support_1', 'N/A'))
                target = kl.get('target', 'N/A')
                report.append(f"- **Kháng Cự:** {res}")
                report.append(f"- **Hỗ Trợ:** {sup}")
                report.append(f"- **Mục Tiêu:** {target}")

            if context.opinions:
                report.append("\n---\n### 🤖 Ý Kiến Từ Các Agent Chuyên Gia")
                for agent_name, agent_opinion in context.opinions.items():
                    report.append(f"\n**{agent_name.upper()} Agent:**")
                    report.append(f"- Tín hiệu: {agent_opinion.signal.value if hasattr(agent_opinion.signal, 'value') else str(agent_opinion.signal)}")
                    # Truncate reasoning for summary
                    reason = agent_opinion.reasoning
                    if len(reason) > 200: reason = reason[:200] + "..."
                    report.append(f"- Nhận định: {reason}")

            llm_analysis = "\n".join(report)
            
            return {
                "symbol": symbol,
                "status": "success",
                "info": context.data.get("stock_info", {}),
                "quote": context.data.get("realtime_quote", {}),
                "circuit_breaker": context.data.get("circuit_breaker", {}), 
                "tech_summary": "Phân tích bởi Multi-Agent System",
                "llm_analysis": llm_analysis,
                "is_multi_agent": True,
                "opinion": {
                    "signal": opinion.signal.value if hasattr(opinion.signal, 'value') else str(opinion.signal),
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
