import json
import re

def parse_json_robustly(text: str) -> dict:
    """
    Parses a JSON string robustly, handling markdown code blocks,
    trailing commas, and conversational text.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string.")

    # Strategy 1: Direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        extracted = match.group(1)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # Maybe the extracted block has trailing commas
            cleaned = re.sub(r',\s*([}\]])', r'\1', extracted)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    # Strategy 3: Extract content between the first '{' and the last '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        extracted = text[start_idx:end_idx+1]
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # We will fall through to Strategy 4 with this extracted block
            pass
    else:
        # If no braces found, use original text for manual cleaning
        extracted = text

    # Strategy 4: Manual cleaning (remove trailing commas, fix unescaped quotes)
    cleaned = re.sub(r',\s*([}\]])', r'\1', extracted)
    
    # Simple fix for unescaped quotes within strings (e.g., words like hello"world -> hello\"world)
    cleaned = re.sub(r'(?<=\w)"(?=\w)', r'\"', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
        
    # If all fail, raise ValueError
    raise ValueError("Failed to parse JSON robustly.")
