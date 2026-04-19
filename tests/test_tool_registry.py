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

def test_initial_tools_registration():
    from src.agents.tools.registry import default_registry
    schemas = default_registry.get_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "get_quote" in names
    assert "get_history" in names
    assert "check_circuit_breaker" in names

def test_scoring_tools_registration():
    from src.agents.tools.registry import default_registry
    schemas = default_registry.get_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "calculate_technical_score_tool" in names
    assert "calculate_fundamental_score_tool" in names

def test_scoring_tools_execution():
    from src.agents.tools.registry import default_registry
    import pandas as pd
    from unittest.mock import patch
    
    with patch('src.agents.tools.registry.VNStockProvider') as mock_provider, \
         patch('src.agents.tools.registry.calculate_technical_score', return_value={'score': 80}), \
         patch('src.agents.tools.registry.calculate_f_score', return_value={'score': 7}):
        
        mock_instance = mock_provider.return_value
        mock_instance.get_historical_data.return_value = pd.DataFrame({'close': [1,2,3]})
        mock_instance.get_financial_report.return_value = {'data': {'roa': 0.1}}
        
        tech_result = default_registry.execute("calculate_technical_score_tool", symbol="FPT")
        assert tech_result == {'score': 80}
        
        fund_result = default_registry.execute("calculate_fundamental_score_tool", symbol="FPT")
        assert fund_result == {'score': 7}

def test_scoring_tools_execution_error():
    from src.agents.tools.registry import default_registry
    from unittest.mock import patch
    
    with patch('src.agents.tools.registry.VNStockProvider') as mock_provider:
        mock_instance = mock_provider.return_value
        mock_instance.get_historical_data.side_effect = Exception("API error")
        mock_instance.get_financial_report.side_effect = Exception("API error")
        
        tech_result = default_registry.execute("calculate_technical_score_tool", symbol="FPT")
        assert tech_result == {"error": "Failed to fetch technical data: API error"}
        
        fund_result = default_registry.execute("calculate_fundamental_score_tool", symbol="FPT")
        assert fund_result == {"error": "Failed to fetch fundamental data: API error"}
