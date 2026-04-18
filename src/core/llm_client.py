import os
from litellm import completion


class LiteLLMClient:
    """Wrapper around LiteLLM to handle fallback and routing"""

    def __init__(self):
        primary = os.getenv("LLM_PRIMARY_MODELS", "gpt-4o")
        backup = os.getenv("LLM_BACKUP_MODELS", "gemini-1.5-pro-latest")
        self.models = [primary, backup]

    def generate(
            self,
            prompt: str,
            system_prompt: str = "Bạn là một chuyên gia phân tích chứng khoán Việt Nam.") -> str:
        # Mock for dry run if keys are not set
        api_key = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
        if api_key == "your_gemini_api_key_here" or not api_key:
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
                response = completion(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=2000
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise RuntimeError(
                f"All LLM models failed. Last error: {last_error}")
        return "No LLM models configured."
