import pandas as pd
import pytest
from src.scoring.technical import calculate_technical_score

def test_calculate_technical_score_uptrend():
    # 50 days of data, closing prices increasing
    data = {
        'close': list(range(10, 60)),  # 50 days
        'volume': [1000] * 50
    }
    df = pd.DataFrame(data)
    
    result = calculate_technical_score(df)
    
    assert 'total_score' in result
    assert 'trend' in result
    assert 'rsi' in result
    assert 'volume_ratio' in result
    assert 0 <= result['total_score'] <= 100
    assert result['trend'] == 'uptrend'
    # In a pure uptrend, MA5 > MA20 > MA50
    
def test_calculate_technical_score_downtrend():
    # 50 days of data, closing prices decreasing
    data = {
        'close': list(range(60, 10, -1)),  # 50 days
        'volume': [1000] * 50
    }
    df = pd.DataFrame(data)
    
    result = calculate_technical_score(df)
    
    assert 'total_score' in result
    assert 'trend' in result
    assert 'rsi' in result
    assert 'volume_ratio' in result
    assert 0 <= result['total_score'] <= 100
    assert result['trend'] == 'downtrend'
    # In a pure downtrend, MA5 < MA20 < MA50

def test_calculate_technical_score_high_rsi_penalty():
    # 50 days of data, closing prices increasing fast causing RSI > 70
    data = {
        'close': [10 + i**2 for i in range(50)], 
        'volume': [1000] * 50
    }
    df = pd.DataFrame(data)
    
    result = calculate_technical_score(df)
    
    assert 'total_score' in result
    assert 'rsi' in result
    assert result['rsi'] > 70
    # The score should be penalized for overbought
    # Total score should not be 100, maybe lower than a perfect uptrend
