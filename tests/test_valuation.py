import pandas as pd
from src.scoring.valuation import DCFEngine, DCFAssumptions

def test_dcf_undervalued():
    # Setup bundle with growing FCF
    # Years: 2021, 2022, 2023
    cf_data = {
        "Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh": [100e9, 120e9, 150e9],
        "Tiền chi để mua sắm, xây dựng TSCĐ": [-20e9, -25e9, -30e9]
    }
    cf_df = pd.DataFrame(cf_data)
    
    financials_bundle = {
        "cash_flow": cf_df,
        "shares_outstanding": 100e6, # 100M shares
    }
    
    # FCF = [80B, 95B, 120B] -> base = 98.33B
    # Market price = 10,000 VND -> Market Cap = 1T VND
    market_price = 10000
    
    engine = DCFEngine()
    result = engine.compute(financials_bundle, market_price)
    
    assert result.fcf_trend == "GROWING"
    assert result.intrinsic_value_per_share > market_price
    # With 15% growth for 5 years, then fade, intrinsic value should be significantly higher than 10k
    assert result.grade == "UNDERVALUED"

def test_dcf_negative_fcf():
    cf_data = {
        "Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh": [-10e9, -20e9, -30e9],
        "Tiền chi để mua sắm, xây dựng TSCĐ": [-10e9, -10e9, -10e9]
    }
    cf_df = pd.DataFrame(cf_data)
    
    financials_bundle = {
        "cash_flow": cf_df,
        "shares_outstanding": 100e6,
    }
    
    engine = DCFEngine()
    result = engine.compute(financials_bundle, 50000)
    
    assert result.grade == "SPECULATIVE"
    assert result.fcf_trend == "NEGATIVE"
    assert result.intrinsic_value_per_share is None
    assert any("FCF âm liên tục" in note for note in result.notes)

def test_dcf_banking_sector():
    financials_bundle = {
        "cash_flow": pd.DataFrame({"dummy": [1, 2, 3]}),
        "shares_outstanding": 100e6,
    }
    
    engine = DCFEngine()
    result = engine.compute(financials_bundle, 20000, industry="Ngân hàng TMCP Ngoại thương")
    
    assert result.grade == "SPECULATIVE"
    assert any("ngành tài chính" in note for note in result.notes)

def test_dcf_small_cap_adjustment():
    # Growing FCF but small cap
    cf_data = {
        "Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh": [10e9, 12e9, 15e9],
        "Tiền chi để mua sắm, xây dựng TSCĐ": [-2e9, -2e9, -2e9]
    }
    cf_df = pd.DataFrame(cf_data)
    
    # Market Cap = 10,000 * 50,000,000 = 500B VND (< 1000B)
    financials_bundle = {
        "cash_flow": cf_df,
        "shares_outstanding": 50e6,
    }
    
    engine = DCFEngine()
    # Before compute, discount rate is 12%
    assert engine.a.discount_rate == 0.12
    
    result = engine.compute(financials_bundle, 10000)
    
    assert engine.a.discount_rate == 0.14
    assert any("vốn hoá nhỏ" in note for note in result.notes)

def test_dcf_zero_shares():
    financials_bundle = {
        "cash_flow": pd.DataFrame({"ocf": [1, 2, 3]}),
        "shares_outstanding": 0,
    }
    engine = DCFEngine()
    result = engine.compute(financials_bundle, 10000)
    assert result.grade == "SPECULATIVE"
    assert any("số lượng cổ phiếu" in note for note in result.notes)

def test_dcf_sensitivity():
    cf_data = {
        "Lưu chuyển tiền tệ thuần từ hoạt động kinh doanh": [100e9, 120e9, 150e9],
        "Tiền chi để mua sắm, xây dựng TSCĐ": [-20e9, -25e9, -30e9]
    }
    cf_df = pd.DataFrame(cf_data)
    financials_bundle = {
        "cash_flow": cf_df,
        "shares_outstanding": 100e6,
    }
    
    engine1 = DCFEngine(DCFAssumptions(discount_rate=0.12))
    res1 = engine1.compute(financials_bundle, 50000)
    
    engine2 = DCFEngine(DCFAssumptions(discount_rate=0.14))
    res2 = engine2.compute(financials_bundle, 50000)
    
    assert res2.intrinsic_value_per_share < res1.intrinsic_value_per_share
