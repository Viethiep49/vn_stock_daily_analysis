import inspect
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, List
from src.data_provider.vnstock_provider import VNStockProvider
from src.market.circuit_breaker import CircuitBreakerHandler
from src.scoring.technical import calculate_technical_score
from src.scoring.fundamental import calculate_f_score
from src.news.vn_news_scraper import get_stock_news

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
            if param.annotation is int:
                param_info["type"] = "integer"
            elif param.annotation is float:
                param_info["type"] = "number"
            elif param.annotation is bool:
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

def calculate_technical_score_tool(symbol: str) -> dict:
    """Tính điểm kỹ thuật (Technical Score) cho một mã cổ phiếu."""
    try:
        provider = VNStockProvider()
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=150)).strftime('%Y-%m-%d')
        df = provider.get_historical_data(symbol, start_date, end_date)
        if df is None or getattr(df, "empty", True):
            return {"error": f"No historical data found for {symbol}"}
        return calculate_technical_score(df)
    except Exception as e:
        return {"error": f"Failed to fetch technical data: {str(e)}"}

def calculate_fundamental_score_tool(symbol: str) -> dict:
    """Tính điểm cơ bản (Fundamental Piotroski F-Score) cho một mã cổ phiếu."""
    try:
        provider = VNStockProvider()
        report = provider.get_financial_report(symbol)
        if not report or 'data' not in report:
            return {"error": f"No fundamental data found for {symbol}"}
        
        import pandas as pd
        df = pd.DataFrame([report['data']])
        return calculate_f_score(df)
    except Exception as e:
        return {"error": f"Failed to fetch fundamental data: {str(e)}"}

def get_stock_news_tool(symbol: str):
    """Lấy danh sách tin tức mới nhất về một mã cổ phiếu."""
    try:
        return get_stock_news(symbol)
    except Exception as e:
        return {"error": f"Failed to fetch news: {str(e)}"}

default_registry = ToolRegistry()
default_registry.register("get_quote", get_quote)
default_registry.register("get_history", get_history)
default_registry.register("check_circuit_breaker", check_circuit_breaker)
default_registry.register("calculate_technical_score_tool", calculate_technical_score_tool)
default_registry.register("calculate_fundamental_score_tool", calculate_fundamental_score_tool)
default_registry.register("get_stock_news_tool", get_stock_news_tool)
