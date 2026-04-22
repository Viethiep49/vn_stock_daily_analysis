import pandas as pd

def calculate_technical_score(df: pd.DataFrame) -> dict:
    """
    Calculate a hard-coded technical score for a given stock DataFrame.
    Expects columns 'close' and 'volume'.
    
    Returns a dict with 'total_score', 'trend', 'rsi', and 'volume_ratio'.
    """
    if len(df) < 50:
        return {
            'total_score': 0,
            'trend': 'insufficient_data',
            'rsi': 50,
            'volume_ratio': 1.0,
            'ma5': 0,
            'ma20': 0,
            'ma50': 0
        }
        
    df = df.copy()
    
    # Calculate MAs
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    
    # Calculate Volume Average (20 days)
    df['vol_ma20'] = df['volume'].rolling(window=20).mean()
    
    # Calculate RSI (14 period)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Fill NaN from division by zero in RSI
    df['rsi'] = df['rsi'].fillna(100)
    
    # Get latest values
    latest = df.iloc[-1]
    
    ma5 = latest['ma5']
    ma20 = latest['ma20']
    ma50 = latest['ma50']
    rsi = latest['rsi']
    current_vol = latest['volume']
    vol_ma20 = latest['vol_ma20']
    
    volume_ratio = current_vol / vol_ma20 if vol_ma20 > 0 else 1.0
    
    # Score calculation
    score = 50  # Base score
    trend = 'neutral'
    
    # Trend alignment
    if ma5 > ma20 and ma20 > ma50:
        score += 30
        trend = 'uptrend'
    elif ma5 < ma20 and ma20 < ma50:
        score -= 20
        trend = 'downtrend'
    elif ma5 > ma20:
        score += 10
        trend = 'weak_uptrend'
    elif ma5 < ma20:
        score -= 10
        trend = 'weak_downtrend'
        
    # RSI penalty/bonus
    if rsi > 70:
        # Overbought
        score -= 20
    elif rsi < 30:
        # Oversold (could be a buying opportunity, but might also be strong downtrend)
        # Let's say it adds a small bounce probability score
        score += 10
    elif 40 <= rsi <= 60:
        # Healthy momentum
        score += 10
        
    # Volume confirmation
    if volume_ratio > 1.2 and trend in ['uptrend', 'weak_uptrend']:
        score += 10
    elif volume_ratio > 1.2 and trend in ['downtrend', 'weak_downtrend']:
        score -= 10
        
    # Clamp score to 0-100
    score = max(0, min(100, score))
    
    return {
        'total_score': score,
        'trend': trend,
        'rsi': rsi,
        'volume_ratio': volume_ratio,
        'ma5': ma5,
        'ma20': ma20,
        'ma50': ma50
    }
