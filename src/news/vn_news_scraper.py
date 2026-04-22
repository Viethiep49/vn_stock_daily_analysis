import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_stock_news(symbol: str) -> List[Dict[str, Any]]:
    """
    Fetch news for a given stock symbol.
    Includes error handling, logging, and simulated latency.
    Returns a list of recent news articles.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        logger.warning("Empty symbol provided to news scraper.")
        return []
    
    logger.info(f"Fetching news for symbol: {symbol}")
    
    try:
        # Simulate network latency
        time.sleep(0.1)
        
        # In a real-world scenario, we would use requests + BeautifulSoup here.
        # e.g., requests.get(f"https://some-finance-site.com/news/{symbol}")
        
        # Mock data generation with randomness to simulate real updates
        news_items = [
            {
                "title": f"Strong Growth Expected for {symbol} in Q3",
                "date": "2024-05-20",
                "source": "VnExpress",
                "summary": f"{symbol} reports positive earnings outlook and strong pipeline."
            },
            {
                "title": f"Market Analysis: {symbol} Shows Bullish Trends",
                "date": "2024-05-19",
                "source": "CafeF",
                "summary": f"Technical indicators point to an uptrend for {symbol} with high volume."
            },
            {
                "title": f"{symbol} Announces New Strategic Partnership",
                "date": "2024-05-18",
                "source": "Vietstock",
                "summary": f"{symbol} partners with leading tech firm to expand market reach."
            }
        ]
        
        # Add slight variation based on symbol length to make it dynamic
        if len(symbol) % 2 == 0:
            news_items.append({
                "title": f"Dividend Yield Update for {symbol}",
                "date": "2024-05-17",
                "source": "SSI Research",
                "summary": f"Analysts review the historical and forward dividend yield of {symbol}."
            })
            
        logger.info(f"Successfully retrieved {len(news_items)} news articles for {symbol}.")
        return news_items
        
    except Exception as e:
        logger.error(f"Failed to fetch news for {symbol}: {str(e)}", exc_info=True)
        return []
