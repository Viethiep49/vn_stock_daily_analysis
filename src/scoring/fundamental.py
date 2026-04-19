import pandas as pd

def calculate_f_score(financials_df: pd.DataFrame) -> dict:
    """
    Calculate the 9-point Piotroski F-Score based on standard financial fields.
    """
    if financials_df.empty:
        return {'score': 0, 'details': {}}
    
    row = financials_df.iloc[0]
    
    def get_val(col):
        return row[col] if col in row and pd.notna(row[col]) else 0
    
    roa = get_val('roa_current')
    roa_prev = get_val('roa_prev')
    cfo = get_val('cfo_current')
    leverage = get_val('leverage_current')
    leverage_prev = get_val('leverage_prev')
    current_ratio = get_val('current_ratio_current')
    current_ratio_prev = get_val('current_ratio_prev')
    shares = get_val('shares_current')
    shares_prev = get_val('shares_prev')
    margin = get_val('gross_margin_current')
    margin_prev = get_val('gross_margin_prev')
    turnover = get_val('asset_turnover_current')
    turnover_prev = get_val('asset_turnover_prev')
    
    details = {
        'profitable': bool(roa > 0),
        'positive_cfo': bool(cfo > 0),
        'roa_increasing': bool(roa > roa_prev),
        'accruals': bool(cfo > roa),
        'leverage_decreasing': bool(leverage < leverage_prev) and bool(leverage_prev > 0),
        'liquidity_increasing': bool(current_ratio > current_ratio_prev),
        'no_dilution': bool(shares <= shares_prev) and bool(shares > 0),
        'margin_increasing': bool(margin > margin_prev),
        'turnover_increasing': bool(turnover > turnover_prev),
    }
    
    score = sum(details.values())
    return {'score': score, 'details': details}
