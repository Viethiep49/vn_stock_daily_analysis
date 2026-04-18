import logging
from typing import List, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseDataProvider

logger = logging.getLogger(__name__)


class FallbackRouter:
    """Router với retry logic và circuit breaker pattern"""

    def __init__(
            self,
            providers: List[BaseDataProvider],
            max_retries: int = 3):
        self.providers = providers
        self.max_retries = max_retries
        self._failure_counts = {id(p): 0 for p in providers}
        self._circuit_open = {id(p): False for p in providers}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def execute_with_fallback(self, operation: str, *args, **kwargs) -> Any:
        last_error = None

        for provider in self.providers:
            provider_id = id(provider)
            if self._circuit_open.get(provider_id):
                continue

            try:
                method = getattr(provider, operation)
                result = method(*args, **kwargs)
                self._failure_counts[provider_id] = 0
                return result

            except Exception as e:
                last_error = e
                self._failure_counts[provider_id] += 1
                logger.warning(
                    f"Provider {provider.__class__.__name__} failed on {operation}: {e}")

                if self._failure_counts[provider_id] >= 5:
                    self._circuit_open[provider_id] = True
                    logger.error(
                        f"Circuit breaker opened for provider {provider.__class__.__name__}")
                continue

        raise RuntimeError(
            f"All providers failed for {operation}. Last error: {last_error}")
