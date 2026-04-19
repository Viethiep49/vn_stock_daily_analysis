import pytest
from src.agents.tools.registry import ToolRegistry

def test_register_and_execute():
    registry = ToolRegistry()
    
    def add(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b
    
    registry.register("add", add)
    result = registry.execute("add", a=1, b=2)
    assert result == 3

def test_get_schemas():
    registry = ToolRegistry()
    
    def get_weather(location: str):
        """Get the current weather in a given location."""
        return f"Weather in {location} is sunny"
    
    registry.register("get_weather", get_weather)
    schemas = registry.get_schemas()
    
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "get_weather"
    assert "location" in schemas[0]["function"]["parameters"]["properties"]
