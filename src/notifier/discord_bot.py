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
                    "value": f"{quote.get('price'):,.0f} đ",
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
                    "value": f"{quote.get('price'):,.0f} đ",
                    "inline": True
                }
            ]

        embed = {
            "title": f"Báo Cáo Phân Tích Cổ Phiếu: {symbol}",
            "description": description,
            "fields": fields
        }

        if cb and cb.get('warning'):
            embed["fields"].append({
                "name": "⚠️ Cảnh Báo",
                "value": cb.get('warning'),
                "inline": False
            })
            embed["color"] = 15158332  # Red if warning
        elif opinion:
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
