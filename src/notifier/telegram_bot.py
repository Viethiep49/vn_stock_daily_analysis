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
            response = requests.post(url, json=payload)
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
        llm = report_data.get('llm_analysis', 'No analysis')

        message = f"📊 *VN STOCK REPORT: {symbol}*\n\n"
        message += f"🏢 *Công ty*: {info.get('company_name')} | {info.get('industry')}\n"
        message += f"💰 *Giá*: {quote.get('price'):,.0f} đ\n"

        if cb and cb.get('warning'):
            message += f"⚠️ *Cảnh báo*: {cb.get('warning')}\n"

        message += f"\n🤖 *Nhận định LLM*:\n{llm}\n"
        message += "\n---"

        return self.send_message(message)
