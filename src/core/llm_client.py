import os
import logging
from typing import Any, Optional
from litellm import completion

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """Wrapper around LiteLLM với OpenRouter fallback và hỗ trợ truyền model động"""

    def __init__(self):
        self.primary_default = os.getenv("LLM_PRIMARY_MODEL", "openrouter/google/gemma-4-26b-a4b-it:free")
        self.backup_default = os.getenv("LLM_BACKUP_MODEL", "openrouter/nvidia/nemotron-3-super-120b-a12b:free")

    def _has_api_key(self) -> bool:
        return bool(
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("OPENAI_API_KEY")
        )

    def generate(
            self,
            prompt: str,
            system_prompt: str = "Bạn là một chuyên gia phân tích chứng khoán Việt Nam.",
            model: Optional[str] = None) -> str:
        
        if not self._has_api_key():
            return "MOCK ANALYSIS: Hệ thống chưa có API Key. Vui lòng kiểm tra file .env."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat(messages, model=model)
        if hasattr(response, 'choices'):
            return response.choices[0].message.content
        return str(response)

    def chat(self, messages: list, model: Optional[str] = None, tools: list = None, tool_choice: str = "auto") -> Any:
        if not self._has_api_key():
            return self._mock_response("No API key provided.")

        # Xác định danh sách model sẽ thử (ưu tiên model được truyền vào)
        models_to_try = [model] if model else [self.primary_default, self.backup_default]
        
        last_error = None
        for target_model in models_to_try:
            if not target_model:
                continue
            try:
                kwargs = dict(
                    model=target_model, 
                    messages=messages, 
                    temperature=0.2, 
                    max_tokens=2000
                )
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice
                
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                if openrouter_key and target_model.startswith("openrouter/"):
                    kwargs["api_key"] = openrouter_key
                    kwargs["extra_body"] = {"include_reasoning": True}
                
                response = completion(**kwargs)
                
                # Log reasoning tokens
                if hasattr(response, 'usage') and hasattr(response.usage, 'extra_fields'):
                    reasoning = response.usage.extra_fields.get('reasoning_tokens')
                    if reasoning:
                        logger.info(f"Reasoning tokens used: {reasoning}")
                
                return response
            except Exception as e:
                logger.warning(f"Model {target_model} failed: {e}")
                last_error = e
                continue

        if last_error:
            raise RuntimeError(f"Tất cả LLM models đã thử đều thất bại. Lỗi cuối: {last_error}")
        raise RuntimeError("Chưa cấu hình LLM model.")

    def _mock_response(self, content: str):
        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(content)]
        class MockChoice:
            def __init__(self, content):
                self.message = MockMessage(content)
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.tool_calls = None
                self.role = "assistant"
        return MockResponse(content)
