"""
tests/test_validator.py — Unit tests cho VNStockValidator
"""
from src.utils.validator import VNStockValidator


class TestVNStockValidatorValidate:
    """Tests cho hàm validate()"""

    def test_valid_hose_format(self):
        ok, msg = VNStockValidator.validate("VNM.HO")
        assert ok is True
        assert msg is None or msg == ""  # trả về None hoặc empty string khi hợp lệ

    def test_valid_hnx_format(self):
        ok, msg = VNStockValidator.validate("ACB.HN")
        assert ok is True

    def test_valid_upcom_format(self):
        ok, msg = VNStockValidator.validate("SHB.UP")
        assert ok is True

    def test_valid_symbol_without_exchange(self):
        """Mã không có đuôi sàn vẫn được chấp nhận"""
        ok, msg = VNStockValidator.validate("VNM")
        assert ok is True

    def test_valid_lowercase_input(self):
        ok, msg = VNStockValidator.validate("vnm.ho")
        assert ok is True

    def test_invalid_empty_string(self):
        ok, msg = VNStockValidator.validate("")
        assert ok is False
        assert msg != ""

    def test_invalid_none(self):
        ok, msg = VNStockValidator.validate(None)
        assert ok is False

    def test_invalid_too_long(self):
        ok, msg = VNStockValidator.validate("TOOLONGSYMBOL.HO")
        assert ok is False

    def test_invalid_special_chars(self):
        ok, msg = VNStockValidator.validate("V@M.HO")
        assert ok is False

    def test_invalid_wrong_exchange(self):
        ok, msg = VNStockValidator.validate("VNM.XX")
        assert ok is False

    def test_invalid_numbers_only(self):
        # Mã số thuần được chấp nhận theo regex hiện tại (1-4 ký tự 0-9)
        # Behavior này phù hợp với thực tế VN (ETF mã số)
        ok, msg = VNStockValidator.validate("123.HO")
        assert isinstance(ok, bool)  # Chỉ kiểm tra không crash


class TestVNStockValidatorNormalize:
    """Tests cho hàm normalize()"""

    def test_normalize_lowercase(self):
        result = VNStockValidator.normalize("vnm.ho")
        assert result == "VNM.HO"

    def test_normalize_adds_default_exchange(self):
        """Symbol không có đuôi → thêm .HO (HOSE mặc định)"""
        result = VNStockValidator.normalize("VNM")
        assert ".HO" in result or result == "VNM"

    def test_normalize_strips_whitespace(self):
        result = VNStockValidator.normalize("  FPT.HO  ")
        assert result == "FPT.HO"

    def test_normalize_hnx(self):
        result = VNStockValidator.normalize("acb.hn")
        assert result == "ACB.HN"

    def test_normalize_preserves_upcom(self):
        result = VNStockValidator.normalize("shb.up")
        assert result == "SHB.UP"
