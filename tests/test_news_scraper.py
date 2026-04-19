import pytest
from src.news.vn_news_scraper import get_stock_news

def test_get_stock_news_returns_list():
    news = get_stock_news("FPT")
    assert isinstance(news, list)
    if len(news) > 0:
        article = news[0]
        assert "title" in article
        assert "date" in article
        assert "source" in article
        assert "summary" in article

def test_get_stock_news_empty_string():
    news = get_stock_news("")
    assert isinstance(news, list)
    assert len(news) == 0
