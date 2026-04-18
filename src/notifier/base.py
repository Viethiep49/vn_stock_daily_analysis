from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseNotifier(ABC):
    """Abstract base class for all notification channels"""

    @abstractmethod
    def send_message(self, message: str) -> bool:
        """Send a simple text message"""
        pass

    @abstractmethod
    def send_report(self, report_data: Dict[str, Any]) -> bool:
        """Send a structured report nicely formatted"""
        pass
