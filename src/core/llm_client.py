import os
from litellm import completion


class LiteLLMClient:
    """Wrapper around LiteLLM với OpenRouter fallback"""

    def __init__(self):
        primary = os.getenv("LLM_PRIMARY_MODEL", "openrouter/google/gemma-3-27b-it:free")
        backup = os.getenv("LLM_BACKUP_MODEL", "openrouter/meta-llama/llama-4-scout:free")
        self.models = [primary, backup]

    def _has_api_key(self) -> bool:
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        return bool(openrouter_key or gemini_key or openai_key)

    def generate(
            self,
            prompt: str,
            system_prompt: str = "Bạn là một chuyên gia phân tích chứng khoán Việt Nam.") -> str:
        if not self._has_api_key():
            return "MOCK ANALYSIS: Cổ phiếu này đang có dấu hiệu tích cực. Khuyến nghị GIỮ."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        last_error = None
        for model in self.models:
            if not model:
                continue
            try:
                kwargs = dict(model=model, messages=messages, temperature=0.2, max_tokens=2000)
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                if openrouter_key and model.startswith("openrouter/"):
                    kwargs["api_key"] = openrouter_key
                response = completion(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise RuntimeError(f"All LLM models failed. Last error: {last_error}")
        return "No LLM models configured."
