import os
from dotenv import load_dotenv
from openai import OpenAI
import litellm
import sys

# Load cấu hình từ .env
load_dotenv()

def test_nemotron_reasoning():
    print("\n--- Testing Nemotron Reasoning (Multi-turn) ---")
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    model_name = "nvidia/nemotron-3-super-120b-a12b:free"
    print(f"Calling model: {model_name}...")

    try:
        # First API call with reasoning
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "How many r's are in the word 'strawberry'?"
                }
            ],
            extra_body={"reasoning": {"enabled": True}}
        )

        # Extract the assistant message
        assistant_msg = response.choices[0].message
        print(f"Step 1 Response: {assistant_msg.content}")
        
        # Check for reasoning_details (if supported and enabled)
        reasoning = getattr(assistant_msg, "reasoning_details", "N/A")
        print(f"Step 1 Reasoning: {reasoning}")

        # Preserve the assistant message with reasoning_details for context
        messages = [
            {"role": "user", "content": "How many r's are in the word 'strawberry'?"},
            {
                "role": "assistant",
                "content": assistant_msg.content,
                "reasoning_details": getattr(assistant_msg, "reasoning_details", None)
            },
            {"role": "user", "content": "Are you sure? Think carefully."}
        ]

        print("\nCalling step 2 (Continuing reasoning)...")
        # Second API call - model continues reasoning from where it left off
        response2 = client.chat.completions.create(
            model=model_name,
            messages=messages,
            extra_body={"reasoning": {"enabled": True}}
        )
        
        print(f"Step 2 Response: {response2.choices[0].message.content}")

    except Exception as e:
        print(f"Error during Nemotron test: {str(e)}")

if __name__ == "__main__":
    # Fix encoding for Windows console
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    test_nemotron_reasoning()
