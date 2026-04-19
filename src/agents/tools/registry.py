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
