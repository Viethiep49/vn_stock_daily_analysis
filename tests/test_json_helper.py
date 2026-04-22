import pytest
from src.utils.json_helper import parse_json_robustly

def test_parse_clean_json():
    text = '{"key": "value", "number": 42}'
    result = parse_json_robustly(text)
    assert result == {"key": "value", "number": 42}

def test_parse_fenced_json():
    text = '''```json
{
    "key": "value"
}
```'''
    result = parse_json_robustly(text)
    assert result == {"key": "value"}

def test_parse_fenced_json_without_lang():
    text = '''```
{"key": "value"}
```'''
    result = parse_json_robustly(text)
    assert result == {"key": "value"}

def test_parse_json_with_conversational_text():
    text = 'Here is your response:\n\n{"status": "success"}\n\nLet me know if you need anything else.'
    result = parse_json_robustly(text)
    assert result == {"status": "success"}

def test_parse_json_with_trailing_comma():
    text = '{"key": "value", "list": [1, 2, 3,],}'
    result = parse_json_robustly(text)
    assert result == {"key": "value", "list": [1, 2, 3]}

def test_parse_json_with_unescaped_quotes():
    # We will test a case where quotes are between word characters, e.g., 'hello"world'
    text_invalid = '{"message": "hello"world"}'
    result = parse_json_robustly(text_invalid)
    assert result == {"message": 'hello"world'}

def test_parse_invalid_json():
    text = 'This is not JSON at all'
    with pytest.raises(ValueError):
        parse_json_robustly(text)
