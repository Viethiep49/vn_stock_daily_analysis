import pandas as pd
from src.scoring.fundamental import calculate_f_score

def test_high_f_score():
    data = {
        'roa_current': [0.05], 'roa_prev': [0.04],
        'cfo_current': [0.06],
        'leverage_current': [0.4], 'leverage_prev': [0.5],
        'current_ratio_current': [2.0], 'current_ratio_prev': [1.5],
        'shares_current': [100], 'shares_prev': [100],
        'gross_margin_current': [0.4], 'gross_margin_prev': [0.35],
        'asset_turnover_current': [1.2], 'asset_turnover_prev': [1.1],
    }
    df = pd.DataFrame(data)
    result = calculate_f_score(df)
    assert result['score'] == 9
    assert all(result['details'].values())

def test_low_f_score():
    data = {
        'roa_current': [-0.05], 'roa_prev': [-0.04],
        'cfo_current': [-0.06],
        'leverage_current': [0.6], 'leverage_prev': [0.5],
        'current_ratio_current': [1.0], 'current_ratio_prev': [1.5],
        'shares_current': [110], 'shares_prev': [100],
        'gross_margin_current': [0.3], 'gross_margin_prev': [0.35],
        'asset_turnover_current': [1.0], 'asset_turnover_prev': [1.1],
    }
    df = pd.DataFrame(data)
    result = calculate_f_score(df)
    assert result['score'] == 0
    assert not any(result['details'].values())

def test_missing_data():
    df = pd.DataFrame([{'roa_current': 0.05}])
    result = calculate_f_score(df)
    assert result['score'] == 2
    assert result['details']['profitable']
    assert result['details']['roa_increasing']
