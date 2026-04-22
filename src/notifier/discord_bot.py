import os
import requests
import logging
from typing import Dict, Any
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """Notification via Discord Webhook"""

    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.is_configured = bool(self.webhook_url)

    def send_message(self, message: str) -> bool:
        if not self.is_configured:
            logger.warning("Discord Webhook is not configured.")
            return False

        payload = {
            "content": message
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Sent message to Discord successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False

    def send_report(self, report_data: Dict[str, Any]) -> bool:
        if not self.is_configured:
            return False

        symbol = report_data.get('symbol', 'Unknown')
        info = report_data.get('info', {})
        quote = report_data.get('quote', {})
        cb = report_data.get('circuit_breaker', {})
        opinion = report_data.get('opinion')
        
        # New Scoring Engine data
        report = report_data.get('report')
        score_field = None
        breakdown_field = None
        risk_field = None
        macro_field = None
        valuation_field = None
        if report:
            score_field = {
                "name": "⭐ Score & Signal",
                "value": f"**{report.composite:.1f}/100** | **{report.final_signal.value}**",
                "inline": True
            }
            breakdown_lines = "\n".join(
                f"`{card.strategy_name}`: {card.score} | {card.signal.value}"
                for card in report.cards
            )
            breakdown_field = {
                "name": "📋 Scorecard Breakdown",
                "value": breakdown_lines or "N/A",
                "inline": False
            }
            
            # Add Risk Metrics
            if report.risk and report.risk.risk_grade != "UNKNOWN":
                risk = report.risk
                risk_field = {
                    "name": f"📉 Rủi ro ({risk.risk_grade})",
                    "value": (
                        f"• Volatility: `{risk.volatility_annual:.1f}%/năm`\n"
                        f"• Sharpe: `{risk.sharpe_ratio:.2f}` | Sortino: `{risk.sortino_ratio:.2f}`\n"
                        f"• VaR 95% 1D: `{risk.var_95_1d:.2f}%`\n"
                        f"• Max DD: `{risk.max_drawdown:.1f}%` | Hiện tại DD: `{risk.current_drawdown:.1f}%`"
                    ),
                    "inline": False
                }
            
            # Add Macro Overlay
            if report.macro:
                m = report.macro
                macro_value = (
                    f"• Fed Funds: `{m.fed_funds_rate:.2f}%` ({m.fed_funds_rate_delta_30d:+.2f} 30D)\n"
                    f"• DXY: `{m.dxy:.2f}` ({m.dxy_delta_30d_pct:+.2f}% 30D)\n"
                    f"• US10Y: `{m.us10y:.2f}%` | Curve 10Y-2Y: `{m.yield_curve_10y_2y:+.2f}`\n"
                    f"• VIX: `{m.vix:.1f}`"
                )
                if m.notes:
                    macro_value += "\n" + "\n".join([f"⚠️ {note}" for note in m.notes])
                
                macro_title = f"🌐 Macro Overlay ({m.regime})"
                if m.regime == "RISK_OFF":
                    macro_title = "⚠️ " + macro_title
                    
                macro_field = {
                    "name": macro_title,
                    "value": macro_value,
                    "inline": False
                }

            # Add DCF Valuation
            if report.valuation:
                v = report.valuation
                if v.intrinsic_value_per_share or v.grade == "SPECULATIVE":
                    val_value = ""
                    if v.intrinsic_value_per_share:
                        val_value = (
                            f"• Intrinsic: `{v.intrinsic_value_per_share:,.0f}đ/cp`\n"
                            f"• Market: `{v.market_price:,.0f}đ/cp`\n"
                            f"• Upside: `{v.upside_pct:+.1f}%` | MoS: `{v.margin_of_safety_pct:.1f}%`\n"
                            f"• FCF base: `{v.fcf_base:,.0f}đ` ({v.fcf_trend})"
                        )
                    
                    if v.notes:
                        if val_value:
                            val_value += "\n"
                        val_value += "\n".join([f"⚠️ {note}" for note in v.notes])
                        
                    valuation_field = {
                        "name": f"💎 Định giá DCF ({v.grade})",
                        "value": val_value or "N/A",
                        "inline": False
                    }

        if opinion:
            description = f"**💡 Lời khuyên:** _{opinion.get('operation_advice')}_\n\n"
            description += f"**📝 Phân tích:**\n{opinion.get('reasoning')[:2000]}"
            
            fields = [
                {
                    "name": "🏢 Công ty",
                    "value": f"{info.get('company_name')} | {info.get('industry')}",
                    "inline": False
                },
                {
                    "name": "💰 Giá Cập Nhật",
                    "value": f"{quote.get('price', 0):,.0f} đ",
                    "inline": True
                },
                {
                    "name": "🎯 Tín Hiệu",
                    "value": f"{opinion.get('signal')} ({opinion.get('confidence')*100:.0f}%)",
                    "inline": True
                },
                {
                    "name": "🌡️ Sentiment",
                    "value": f"{opinion.get('sentiment_score')}/100",
                    "inline": True
                }
            ]

            if opinion.get('key_points'):
                fields.append({
                    "name": "📌 Điểm Nhấn",
                    "value": "\n".join([f"• {p}" for p in opinion.get('key_points')]),
                    "inline": False
                })

            levels = opinion.get('key_levels', {})
            if levels:
                levels_str = f"HT: {levels.get('support', '-')} | KC: {levels.get('resistance', '-')} | Target: {levels.get('target', '-')}"
                fields.append({
                    "name": "📐 Mức Kỹ Thuật",
                    "value": levels_str,
                    "inline": False
                })
        else:
            llm = report_data.get('llm_analysis', 'No analysis')
            description = llm[:4000]
            fields = [
                {
                    "name": "🏢 Công ty",
                    "value": f"{info.get('company_name')} | {info.get('industry')}",
                    "inline": False
                },
                {
                    "name": "💰 Giá Cập Nhật",
                    "value": f"{quote.get('price', 0):,.0f} đ",
                    "inline": True
                }
            ]

        embed = {
            "title": f"Báo Cáo Phân Tích Cổ Phiếu: {symbol}",
            "description": description,
            "fields": fields
        }
        
        if score_field:
            # Insert at second position if possible
            embed["fields"].insert(1, score_field)
            
        if breakdown_field:
            embed["fields"].append(breakdown_field)

        if risk_field:
            embed["fields"].append(risk_field)

        if macro_field:
            embed["fields"].append(macro_field)

        if valuation_field:
            embed["fields"].append(valuation_field)

        if cb and cb.get('warning'):
            embed["fields"].append({
                "name": "⚠️ Cảnh Báo",
                "value": cb.get('warning'),
                "inline": False
            })
            embed["color"] = 15158332  # Red if warning
        
        # Override color if high risk
        if report and report.risk and report.risk.risk_grade in ("HIGH", "EXTREME"):
            embed["color"] = 15158332  # Red
        elif report and report.macro and report.macro.regime == "RISK_OFF":
            if not (cb and cb.get('warning')):
                embed["color"] = 15105570  # Orange (Warning)
        elif not (cb and cb.get('warning')):
            if opinion:
                signal = opinion.get('signal', '').upper()
                if 'BUY' in signal:
                    embed["color"] = 3066993  # Green
                elif 'SELL' in signal:
                    embed["color"] = 15158332  # Red
                else:
                    embed["color"] = 16776960  # Yellow/Gold
            else:
                embed["color"] = 3066993  # Green (Default)

        payload = {
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            logger.info("Sent report to Discord successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord report: {e}")
            return False
