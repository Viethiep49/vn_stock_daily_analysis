"""
tests/test_circuit_breaker.py — Unit tests cho CircuitBreakerHandler
"""
import pytest
from src.market.circuit_breaker import CircuitBreakerHandler, PriceLimitConfig


@pytest.fixture
def cb():
    """Fresh CircuitBreakerHandler với cấu hình mặc định"""
    return CircuitBreakerHandler()


@pytest.fixture
def cb_custom():
    """Handler với cấu hình tùy chỉnh cho kiểm thử"""
    config = PriceLimitConfig(hose_bluechip=0.07, hose_normal=0.07, hnx=0.10, upcom=0.15)
    return CircuitBreakerHandler(config)


class TestSetAndGetRefPrice:
    def test_set_and_retrieve_reference_price(self, cb):
        cb.set_reference_price("VNM.HO", 61.3)
        ceiling, floor = cb.get_price_limits("VNM.HO")
        assert ceiling > 61.3
        assert floor < 61.3

    def test_case_insensitive_symbol(self, cb):
        cb.set_reference_price("vnm.ho", 100.0)
        ceiling, _ = cb.get_price_limits("VNM.HO")
        assert ceiling > 0

    def test_missing_ref_price_raises(self, cb):
        with pytest.raises(ValueError):
            cb.get_price_limits("NOTSET.HO")


class TestPriceLimits:
    """Tests tính toán trần/sàn theo biên độ sàn"""

    def test_hose_ceiling_7_percent(self, cb):
        ref = 100.0
        cb.set_reference_price("VNM.HO", ref)
        ceiling, floor = cb.get_price_limits("VNM.HO")
        assert abs(ceiling - ref * 1.07) < 1.0  # tolerance 1 đơn vị (nghìn đồng)

    def test_hose_floor_7_percent(self, cb):
        ref = 100.0
        cb.set_reference_price("VNM.HO", ref)
        ceiling, floor = cb.get_price_limits("VNM.HO")
        assert abs(floor - ref * 0.93) < 1.0

    def test_hnx_ceiling_10_percent(self, cb):
        ref = 50.0
        cb.set_reference_price("ACB.HN", ref)
        ceiling, floor = cb.get_price_limits("ACB.HN")
        assert abs(ceiling - ref * 1.10) < 1.0

    def test_upcom_ceiling_15_percent(self, cb):
        ref = 20.0
        cb.set_reference_price("XYZ.UP", ref)
        ceiling, floor = cb.get_price_limits("XYZ.UP")
        assert abs(ceiling - ref * 1.15) < 1.0

    def test_ceiling_greater_than_floor(self, cb):
        cb.set_reference_price("FPT.HO", 75.0)
        ceiling, floor = cb.get_price_limits("FPT.HO")
        assert ceiling > floor

    def test_bluechip_same_limit_as_hose(self, cb):
        """VN30 stocks (VNM) có biên độ 7% giống HOSE thường"""
        cb.set_reference_price("VNM.HO", 100.0)
        ceiling, floor = cb.get_price_limits("VNM.HO")
        assert abs(ceiling - 107.0) < 1.0


class TestCheckLimitStatus:
    """Tests kiểm tra trạng thái giá so với trần/sàn"""

    def test_normal_price_no_warning(self, cb):
        cb.set_reference_price("VNM.HO", 60.0)
        status = cb.check_limit_status("VNM.HO", 61.0)
        assert status['is_limit_up'] is False
        assert status['is_limit_down'] is False
        assert status['warning'] is None

    def test_price_at_ceiling_triggers_limit_up(self, cb):
        ref = 60.0
        cb.set_reference_price("VNM.HO", ref)
        ceiling = ref * 1.07
        status = cb.check_limit_status("VNM.HO", ceiling)
        assert status['is_limit_up'] is True
        assert "TRẦN" in status['warning']

    def test_price_at_floor_triggers_limit_down(self, cb):
        ref = 60.0
        cb.set_reference_price("VNM.HO", ref)
        floor = ref * 0.93
        status = cb.check_limit_status("VNM.HO", floor)
        assert status['is_limit_down'] is True
        assert "SÀN" in status['warning']

    def test_status_has_distance_when_normal(self, cb):
        cb.set_reference_price("FPT.HO", 75.0)
        status = cb.check_limit_status("FPT.HO", 76.0)
        assert status['distance_to_ceiling'] is not None
        assert status['distance_to_floor'] is not None
        assert status['distance_to_ceiling'] > 0

    def test_status_returns_symbol(self, cb):
        cb.set_reference_price("HPG.HO", 25.0)
        status = cb.check_limit_status("HPG.HO", 25.5)
        assert status['symbol'] == "HPG.HO"

    def test_status_returns_price_info(self, cb):
        cb.set_reference_price("MWG.HO", 50.0)
        status = cb.check_limit_status("MWG.HO", 51.0)
        assert status['current_price'] == 51.0
        assert status['ceiling'] > 0
        assert status['floor'] > 0


class TestBluechipDetection:
    """Tests phát hiện cổ phiếu bluechip (VN30)"""

    def test_vnm_is_bluechip(self, cb):
        assert cb._is_bluechip("VNM") is True

    def test_vcb_is_bluechip(self, cb):
        assert cb._is_bluechip("VCB") is True

    def test_fpt_is_bluechip(self, cb):
        assert cb._is_bluechip("FPT") is True

    def test_unknown_stock_not_bluechip(self, cb):
        assert cb._is_bluechip("XXXX") is False
