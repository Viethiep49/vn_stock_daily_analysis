import os
import requests
import logging
from typing import Dict, Any
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """Notification via Telegram Bot"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.is_configured = bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> bool:
        if not self.is_configured:
            logger.warning("Telegram Bot is not configured.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            # Use short timeout to avoid blocking
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Sent message to Telegram successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_report(self, report_data: Dict[str, Any]) -> bool:
        symbol = report_data.get('symbol', 'Unknown')
        info = report_data.get('info', {})
        quote = report_data.get('quote', {})
        cb = report_data.get('circuit_breaker', {})
        opinion = report_data.get('opinion')
        llm = report_data.get('llm_analysis', 'No analysis')
        
        # New Scoring Engine data
        report = report_data.get('report')
        score_text = ""
        if report:
            score_text = f"⭐ *Score*: `{report.composite:.1f}/100` | *Signal*: `{report.final_signal.value}`\n"
            score_text += "\n*Chi tiết chiến lược:*\n"
            for card in report.cards:
                score_text += f"- {card.strategy_name}: `{card.score}` | {card.signal.value}\n"
            
            # Add Risk Metrics
            if report.risk and report.risk.risk_grade != "UNKNOWN":
                risk = report.risk
                score_text += f"\n📉 *Rủi ro* (`{risk.risk_grade}`):\n"
                score_text += f"  • Volatility: `{risk.volatility_annual:.1f}%/năm`\n"
                score_text += f"  • Sharpe: `{risk.sharpe_ratio:.2f}` | Sortino: `{risk.sortino_ratio:.2f}`\n"
                score_text += f"  • VaR 95% 1D: `{risk.var_95_1d:.2f}%`\n"
                score_text += f"  • Max DD: `{risk.max_drawdown:.1f}%` | Hiện tại DD: `{risk.current_drawdown:.1f}%`\n"

            # Add DCF Valuation
            if report.valuation:
                v = report.valuation
                if v.intrinsic_value_per_share or v.grade == "SPECULATIVE":
                    score_text += f"\n💎 *Định giá DCF* (`{v.grade}`):\n"
                    if v.intrinsic_value_per_share:
                        score_text += f"  • Intrinsic: `{v.intrinsic_value_per_share:,.0f}đ/cp`\n"
                        score_text += f"  • Market: `{v.market_price:,.0f}đ/cp`\n"
                        score_text += f"  • Upside: `{v.upside_pct:+.1f}%` | MoS: `{v.margin_of_safety_pct:.1f}%`\n"
                        score_text += f"  • FCF base: `{v.fcf_base:,.0f}đ` ({v.fcf_trend})\n"
                    
                    if v.notes:
                        for note in v.notes:
                            score_text += f"⚠️ {note}\n"

        message = f"📊 *VN STOCK REPORT: {symbol}*\n\n"
        message += f"🏢 *Công ty*: {info.get('company_name')} | {info.get('industry')}\n"
        message += f"💰 *Giá*: {quote.get('price', 0) * 1000:,.0f} đ\n"
        message += score_text

        if cb and cb.get('warning'):
            message += f"\n⚠️ *Cảnh báo*: {cb.get('warning')}\n"

        if opinion:
            message += f"\n🎯 *Tín hiệu*: `{opinion.get('signal')}` ({opinion.get('confidence')*100:.0f}%)\n"
            message += f"🌡️ *Sentiment*: `{opinion.get('sentiment_score')}/100`\n"
            message += f"💡 *Lời khuyên*: _{opinion.get('operation_advice')}_\n"
            
            if opinion.get('key_points'):
                message += "\n📌 *Điểm nhấn*:\n"
                for point in opinion.get('key_points'):
                    message += f"• {point}\n"
            
            levels = opinion.get('key_levels', {})
            if levels:
                message += f"\n📐 *Mức kỹ thuật*: HT: {levels.get('support', '-')} | KC: {levels.get('resistance', '-')} | Target: {levels.get('target', '-')}\n"
            
            message += f"\n📝 *Phân tích*:\n{opinion.get('reasoning')}\n"
        else:
            message += f"\n🤖 *Nhận định AI*:\n{llm}\n"

        # Add Macro Overlay
        if report and report.macro:
            m = report.macro
            message += f"\n🌐 *Macro Overlay* (`{m.regime}`):\n"
            message += f"  • Fed Funds: `{m.fed_funds_rate:.2f}%` ({m.fed_funds_rate_delta_30d:+.2f} 30D)\n"
            message += f"  • DXY: `{m.dxy:.2f}` ({m.dxy_delta_30d_pct:+.2f}% 30D)\n"
            message += f"  • US10Y: `{m.us10y:.2f}%` | Curve 10Y-2Y: `{m.yield_curve_10y_2y:+.2f}`\n"
            message += f"  • VIX: `{m.vix:.1f}`\n"
            if m.notes:
                for note in m.notes:
                    message += f"⚠️ {note}\n"

        message += "\n---"

        return self.send_message(message)
