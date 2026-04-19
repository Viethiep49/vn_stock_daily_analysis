"""
tests/test_notifier.py — Unit tests cho TelegramNotifier và DiscordNotifier

Tất cả tests đều mock HTTP requests — không gửi tin nhắn thật.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.notifier.telegram_bot import TelegramNotifier
from src.notifier.discord_bot import DiscordNotifier


# ────────────────────────────────────────────────────────────────────────────
# Sample Report Data
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_report():
    return {
        "symbol": "VNM",
        "status": "success",
        "info": {
            "company_name": "CTCP Sữa Việt Nam",
            "industry": "Thực phẩm",
            "exchange": "HOSE",
        },
        "quote": {
            "price": 61.3,
            "change": 0.2,
            "change_pct": 0.33,
            "volume": 3_115_500,
        },
        "circuit_breaker": None,
        "llm_analysis": "VNM đang trong xu hướng tích cực. Khuyến nghị GIỮ.",
    }


@pytest.fixture
def report_with_warning(sample_report):
    r = dict(sample_report)
    r["circuit_breaker"] = {"warning": "⚠️ VNM đang ở giá TRẦN — Khó mua"}
    return r


@pytest.fixture
def report_with_opinion(sample_report):
    r = dict(sample_report)
    r["opinion"] = {
        "signal": "STRONG_BUY",
        "confidence": 0.95,
        "sentiment_score": 85,
        "operation_advice": "Mua mạnh tại vùng hỗ trợ.",
        "key_points": ["Dòng tiền lớn tham gia", "Đột phá kháng cự"],
        "reasoning": "Phân tích chi tiết...",
        "key_levels": {"support": 60.0, "resistance": 65.0, "target": 70.0}
    }
    return r


# ────────────────────────────────────────────────────────────────────────────
# TelegramNotifier Tests
# ────────────────────────────────────────────────────────────────────────────

class TestTelegramNotifier:
    def test_not_configured_without_env(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        n = TelegramNotifier()
        assert n.is_configured is False

    def test_configured_with_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100123456")
        n = TelegramNotifier()
        assert n.is_configured is True

    def test_send_message_returns_false_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        n = TelegramNotifier()
        result = n.send_message("Test")
        assert result is False

    def test_send_message_calls_telegram_api(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("src.notifier.telegram_bot.requests.post", return_value=mock_response) as mock_post:
            n = TelegramNotifier()
            result = n.send_message("Xin chào!")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]['json']
        assert call_kwargs['chat_id'] == "-100999"
        assert "Xin chào!" in call_kwargs['text']

    def test_send_message_returns_false_on_http_error(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        with patch("src.notifier.telegram_bot.requests.post", side_effect=Exception("Network error")):
            n = TelegramNotifier()
            result = n.send_message("Test")

        assert result is False

    def test_send_report_includes_symbol(self, monkeypatch, sample_report):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        sent_texts = []

        def fake_post(url, json=None, **kwargs):
            sent_texts.append(json.get('text', ''))
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.telegram_bot.requests.post", side_effect=fake_post):
            n = TelegramNotifier()
            n.send_report(sample_report)

        assert len(sent_texts) == 1
        assert "VNM" in sent_texts[0]

    def test_send_report_includes_warning(self, monkeypatch, report_with_warning):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        sent_texts = []

        def fake_post(url, json=None, **kwargs):
            sent_texts.append(json.get('text', ''))
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.telegram_bot.requests.post", side_effect=fake_post):
            n = TelegramNotifier()
            n.send_report(report_with_warning)

        assert "TRẦN" in sent_texts[0]

    def test_send_report_includes_opinion(self, monkeypatch, report_with_opinion):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:TOKEN")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "-100999")

        sent_texts = []

        def fake_post(url, json=None, **kwargs):
            sent_texts.append(json.get('text', ''))
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.telegram_bot.requests.post", side_effect=fake_post):
            n = TelegramNotifier()
            n.send_report(report_with_opinion)

        text = sent_texts[0]
        assert "STRONG_BUY" in text
        assert "Sentiment" in text
        assert "Lời khuyên" in text
        assert "Dòng tiền lớn" in text
        assert "Mức kỹ thuật" in text


# ────────────────────────────────────────────────────────────────────────────
# DiscordNotifier Tests
# ────────────────────────────────────────────────────────────────────────────

class TestDiscordNotifier:
    def test_not_configured_without_webhook(self, monkeypatch):
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
        n = DiscordNotifier()
        assert n.is_configured is False

    def test_configured_with_webhook(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")
        n = DiscordNotifier()
        assert n.is_configured is True

    def test_send_message_returns_false_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
        n = DiscordNotifier()
        result = n.send_message("Test")
        assert result is False

    def test_send_message_calls_discord_webhook(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("src.notifier.discord_bot.requests.post", return_value=mock_response) as mock_post:
            n = DiscordNotifier()
            result = n.send_message("Test message")

        assert result is True
        mock_post.assert_called_once()

    def test_send_report_uses_green_embed_when_no_warning(self, monkeypatch, sample_report):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")

        sent_payloads = []

        def fake_post(url, json=None, **kwargs):
            sent_payloads.append(json)
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.discord_bot.requests.post", side_effect=fake_post):
            n = DiscordNotifier()
            n.send_report(sample_report)

        embed = sent_payloads[0]['embeds'][0]
        assert embed['color'] == 3066993  # green

    def test_send_report_uses_red_embed_when_warning(self, monkeypatch, report_with_warning):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")

        sent_payloads = []

        def fake_post(url, json=None, **kwargs):
            sent_payloads.append(json)
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.discord_bot.requests.post", side_effect=fake_post):
            n = DiscordNotifier()
            n.send_report(report_with_warning)

        embed = sent_payloads[0]['embeds'][0]
        assert embed['color'] == 15158332  # red

    def test_send_report_includes_symbol_in_title(self, monkeypatch, sample_report):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")

        sent_payloads = []

        def fake_post(url, json=None, **kwargs):
            sent_payloads.append(json)
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.discord_bot.requests.post", side_effect=fake_post):
            n = DiscordNotifier()
            n.send_report(sample_report)

        embed = sent_payloads[0]['embeds'][0]
        assert "VNM" in embed['title']

    def test_send_report_includes_opinion(self, monkeypatch, report_with_opinion):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/123/abc")

        sent_payloads = []

        def fake_post(url, json=None, **kwargs):
            sent_payloads.append(json)
            r = MagicMock()
            r.raise_for_status.return_value = None
            return r

        with patch("src.notifier.discord_bot.requests.post", side_effect=fake_post):
            n = DiscordNotifier()
            n.send_report(report_with_opinion)

        embed = sent_payloads[0]['embeds'][0]
        assert "Lời khuyên" in embed['description']
        fields = {f['name']: f['value'] for f in embed['fields']}
        assert "🎯 Tín Hiệu" in fields
        assert "STRONG_BUY" in fields["🎯 Tín Hiệu"]
        assert "🌡️ Sentiment" in fields
        assert "85/100" in fields["🌡️ Sentiment"]
        assert "📌 Điểm Nhấn" in fields
        assert "Dòng tiền lớn" in fields["📌 Điểm Nhấn"]
