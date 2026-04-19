def get_stock_news(symbol: str) -> list:
    """
    Fetch news for a given stock symbol.
    Returns a mock list of recent news articles.
    """
    if not symbol:
        return []
    
    # Mock data
    return [
        {
            "title": f"Strong Growth Expected for {symbol} in Q3",
            "date": "2024-05-20",
            "source": "VnExpress",
            "summary": f"{symbol} reports positive earnings."
        },
        {
            "title": f"Market Analysis: {symbol} Shows Bullish Trends",
            "date": "2024-05-19",
            "source": "CafeF",
            "summary": f"Technical indicators point to an uptrend for {symbol}."
        },
        {
            "title": f"{symbol} Announces New Strategic Partnership",
            "date": "2024-05-18",
            "source": "Vietstock",
            "summary": f"{symbol} partners with leading tech firm."
        }
    ]
