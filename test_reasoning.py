import os
from dotenv import load_dotenv
from openai import OpenAI
import litellm
import sys

# Load cấu hình từ .env
load_dotenv()

def test_with_openai_sdk():
    print("\n--- Testing with OpenAI SDK (OpenRouter) ---")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "sk-or" not in api_key:
        print("❌ Lỗi: Chưa tìm thấy OPENROUTER_API_KEY hợp lệ trong .env")
        return

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        # Su dụng model khac vi Gemma 4 dang bi rate limit
        model_name = "mistralai/mistral-7b-instruct:free"
        print(f"Calling model: {model_name}...")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "How many r's are in the word 'strawberry'?"}],
            extra_body={"reasoning": {"enabled": True}}
        )
        
        msg = response.choices[0].message
        print(f"Assistant Result: {msg.content}")
        
    except Exception as e:
        print(f"OpenAI SDK Error: {str(e)}")

def test_with_litellm():
    print("\n--- Testing with LiteLLM (Project Config) ---")
    model = os.getenv("LLM_PRIMARY_MODEL")
    if not model:
        print("Loi: Chua dinh nghia LLM_PRIMARY_MODEL trong .env")
        return
        
    print(f"Calling LiteLLM with model: {model}...")
    try:
        # LiteLLM thuong can prefix openrouter/
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Xin chao, dự án phân tích chứng khoán này có ổn không?"}],
        )
        print(f"LiteLLM Result: {response.choices[0].message.content}")
    except Exception as e:
        print(f"LiteLLM Error: {str(e)}")

if __name__ == "__main__":
    test_with_openai_sdk()
    test_with_litellm()
