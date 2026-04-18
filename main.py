import argparse
import sys
import io
from dotenv import load_dotenv
import logging

# Fix UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.core.analyzer import Analyzer
from src.notifier.telegram_bot import TelegramNotifier
from src.notifier.discord_bot import DiscordNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="VN Stock Daily Analysis MVP")
    parser.add_argument(
        "--symbol",
        type=str,
        default="VNM.HO",
        help="Mã cổ phiếu cần phân tích (VD: VNM.HO)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chạy local, không push notification")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Chạy theo lịch, chỉ báo cáo nếu có signal hoặc được lập lịch")
    parser.add_argument(
        "--force-run",
        action="store_true",
        help="Bỏ qua việc kiểm tra xem có phải ngày giao dịch không")

    args = parser.parse_args()

    if not args.symbol:
        logger.error("Vui lòng cung cấp mã cổ phiếu. (VD: --symbol VNM.HO)")
        sys.exit(1)

    # TODO: In real implementation, check trading calendar if not force_run
    if args.schedule and not args.force_run:
        logger.info("Chạy chế độ schedule, kiểm tra ngày giao dịch...")
        # from src.market.trading_calendar import is_trading_day
        # if not is_trading_day():
        #     logger.info("Hôm nay không phải ngày giao dịch. Thoát.")
        #     sys.exit(0)

    analyzer = Analyzer()
    result = analyzer.analyze(args.symbol)

    print("\n" + "=" * 50)
    print(f"BÁO CÁO PHÂN TÍCH: {result.get('symbol', args.symbol)}")
    print("=" * 50)

    if result.get("status") == "failed":
        print(f"❌ LỖI: {result.get('error')}")
        sys.exit(1)

    info = result.get("info", {})
    quote = result.get("quote", {})
    cb = result.get("circuit_breaker", {})
    tech = result.get("tech_summary", "")

    # vnstock KBS trả giá theo nghìn đồng → nhân 1000 để hiển thị đúng
    price_vnd = quote.get('price', 0) * 1000
    change_vnd = quote.get('change', 0) * 1000
    change_pct = quote.get('change_pct', 0)

    company = info.get('company_name') or info.get('symbol', '')
    industry = info.get('industry', 'N/A')
    exchange = info.get('exchange', '')

    print(f"🏢 Công ty: {company} | Ngành: {industry} | Sàn: {exchange}")
    print(
        f"💰 Giá:    {price_vnd:,.0f}đ  ({change_vnd:+,.0f}đ / {change_pct:+.2f}%)")
    print(f"📦 KL giao dịch: {quote.get('volume', 0):,.0f} cổ phiếu")
    if tech:
        print(f"📈 Kỹ thuật: {tech}")

    if cb and cb.get('warning'):
        print(f"⚠️  Cảnh báo: {cb.get('warning')}")

    print("-" * 50)
    print("🤖 LLM Analysis:")
    print(result.get("llm_analysis", "No analysis found"))
    print("-" * 50)
    print("✅ Trạng thái: Hoàn thành")

    if not args.dry_run:
        logger.info("Sending notifications...")
        telegram = TelegramNotifier()
        telegram.send_report(result)

        discord = DiscordNotifier()
        discord.send_report(result)
    else:
        logger.info("[Dry Run] Skipped sending notifications.")


if __name__ == "__main__":
    main()
