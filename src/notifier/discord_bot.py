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
        llm = report_data.get('llm_analysis', 'No analysis')

        embed = {
            "title": f"Báo Cáo Phân Tích Cổ Phiếu: {symbol}",
            "description": llm[:4000],  # Discord limits
            "color": 3447003,  # Blue
            "fields": [
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
        }

        if cb and cb.get('warning'):
            embed["fields"].append({
                "name": "⚠️ Cảnh Báo",
                "value": cb.get('warning'),
                "inline": False
            })
            embed["color"] = 15158332  # Red if warning
        else:
            embed["color"] = 3066993  # Green

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
