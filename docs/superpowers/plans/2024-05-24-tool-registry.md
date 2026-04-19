# Tool Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `ToolRegistry` that maps string names to Python functions and generates OpenAI function-calling schemas.

**Architecture:** The `ToolRegistry` will manage a collection of tools. Each tool consists of a function and its metadata. It will provide methods to get schemas for LLMs and to execute functions by name.

**Tech Stack:** Python, LiteLLM/OpenAI Schema format.

---

### Task 1: Setup and Basic ToolRegistry Structure

**Files:**
- Create: `src/agents/tools/registry.py`
- Create: `tests/test_tool_registry.py`

- [ ] **Step 1: Write the failing test for basic registry**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tool_registry.py -v`
Expected: FAIL (Module not found or ToolRegistry not defined)

- [ ] **Step 3: Implement ToolRegistry with schema generation**

```python
import inspect
from typing import Dict, Any, Callable, List

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name](**kwargs)

    def get_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for name, func in self.tools.items():
            schema = self._generate_schema(name, func)
            schemas.append(schema)
        return schemas

    def _generate_schema(self, name: str, func: Callable) -> Dict[str, Any]:
        doc = inspect.getdoc(func) or ""
        sig = inspect.signature(func)
        
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            param_info = {"type": "string"} # Default to string
            # Basic type mapping
            if param.annotation == int:
                param_info["type"] = "integer"
            elif param.annotation == float:
                param_info["type"] = "number"
            elif param.annotation == bool:
                param_info["type"] = "boolean"
                
            parameters["properties"][param_name] = param_info
            if param.default is inspect.Parameter.empty:
                parameters["required"].append(param_name)
                
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": doc,
                "parameters": parameters
            }
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit initial structure**

```bash
git add src/agents/tools/registry.py tests/test_tool_registry.py
git commit -m "feat: implement basic ToolRegistry"
```

---

### Task 2: Register Initial Tools

**Files:**
- Modify: `src/agents/tools/registry.py`
- Modify: `tests/test_tool_registry.py`

- [ ] **Step 1: Write tests for initial tools**

```python
from src.data_provider.vnstock_provider import VNStockProvider
from src.market.circuit_breaker import CircuitBreakerHandler

def test_initial_tools_registration():
    # This might need mocking or a way to verify registration
    from src.agents.tools.registry import default_registry
    schemas = default_registry.get_schemas()
    names = [s["function"]["name"] for s in schemas]
    assert "get_quote" in names
    assert "get_history" in names
    assert "check_circuit_breaker" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tool_registry.py::test_initial_tools_registration -v`
Expected: FAIL (default_registry not defined or tools not registered)

- [ ] **Step 3: Implement initial tools registration**

```python
# src/agents/tools/registry.py

# ... (Previous imports)
from src.data_provider.vnstock_provider import VNStockProvider
from src.market.circuit_breaker import CircuitBreakerHandler

# ... (ToolRegistry class)

def get_quote(symbol: str):
    """Lấy giá realtime của một mã cổ phiếu."""
    return VNStockProvider().get_realtime_quote(symbol)

def get_history(symbol: str, start_date: str, end_date: str):
    """Lấy dữ liệu lịch sử giá của một mã cổ phiếu."""
    df = VNStockProvider().get_historical_data(symbol, start_date, end_date)
    return df.to_dict('records')

def check_circuit_breaker(symbol: str, current_price: float, reference_price: float):
    """Kiểm tra xem giá hiện tại có chạm trần/sàn không."""
    handler = CircuitBreakerHandler()
    handler.set_reference_price(symbol, reference_price)
    return handler.check_limit_status(symbol, current_price)

default_registry = ToolRegistry()
default_registry.register("get_quote", get_quote)
default_registry.register("get_history", get_history)
default_registry.register("check_circuit_breaker", check_circuit_breaker)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/agents/tools/registry.py tests/test_tool_registry.py
git commit -m "feat: add tool registry for agents"
```
