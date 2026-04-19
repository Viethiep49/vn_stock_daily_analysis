# User Guide: Usage & Automation

This guide provides detailed instructions on how to use the VN Stock Daily Analysis tool via the Command Line Interface (CLI) and how to set up automated analysis using GitHub Actions.

## Command Line Interface (CLI)

The tool is primarily used through `main.py`. Ensure your [configuration](configuration.md) is complete before running these commands.

### Basic Analysis

To analyze a single stock symbol:

```bash
python main.py --symbol FPT
```

You can also specify the exchange suffix if needed (e.g., `.HO` for HoSE, `.HN` for HNX):

```bash
python main.py --symbol VNM.HO
```

### Watchlist Management

The tool maintains a local `watchlist.json` file for stocks you want to track regularly.

- **Add a symbol to watchlist**:
  ```bash
  python main.py --watchlist-add HPG
  ```

- **Remove a symbol from watchlist**:
  ```bash
  python main.py --watchlist-remove VNM
  ```

- **Analyze all symbols in watchlist**:
  ```bash
  python main.py --watchlist
  ```
  This will analyze each stock in your watchlist and provide a summary ranking based on their scores.

### Advanced Analysis Modes

- **Multi-Agent Pipeline**:
  Run a more comprehensive analysis using specialized agents (Technical, Risk, Decision):
  ```bash
  python main.py --symbol FPT --agents
  ```

- **Custom Skill/Strategy**:
  Provide additional context or logic to the agents using a markdown file:
  ```bash
  python main.py --symbol FPT --agents --skill docs/skills/VSA.md
  ```

- **Dry Run (Local Only)**:
  Perform analysis without sending notifications to Telegram or Discord:
  ```bash
  python main.py --symbol FPT --dry-run
  ```

- **Force Run**:
  Bypass the trading day check (useful for testing on weekends):
  ```bash
  python main.py --symbol FPT --force-run
  ```

---

## Automation with GitHub Actions

You can automate the daily analysis to run every trading day using GitHub Actions.

### Setup Steps

1. **Fork the Repository**: Ensure you have your own copy of the project on GitHub.
2. **Configure Secrets**:
   Go to your repository settings: **Settings > Secrets and variables > Actions**. Add the following secrets:
   
   | Secret Name | Description | Required |
   |-------------|-------------|----------|
   | `GEMINI_API_KEY` | Google AI API Key | Yes (if using Gemini) |
   | `OPENROUTER_API_KEY`| OpenRouter API Key | Optional |
   | `TELEGRAM_BOT_TOKEN`| Telegram Bot Token | For Telegram notifications |
   | `TELEGRAM_CHAT_ID`  | Telegram Chat ID | For Telegram notifications |
   | `DISCORD_WEBHOOK_URL`| Discord Webhook URL | For Discord notifications |
   | `LLM_PRIMARY_MODEL` | E.g., `gemini/gemini-2.0-flash` | Optional |

3. **Enable Workflow**:
   The workflow is defined in `.github/workflows/daily_analysis.yml`. It is set to run automatically at **15:00 VN Time (08:00 UTC)** every Monday to Friday.

### Manual Trigger

You can also trigger the analysis manually from the GitHub UI:
1. Navigate to the **Actions** tab.
2. Select the **VN Stock Daily Analysis** workflow.
3. Click **Run workflow**.
4. (Optional) Provide a specific symbol or check "Bỏ qua check ngày giao dịch" (Force Run).

---

## Troubleshooting

### 1. API Errors (401/403 Unauthorized)
- **Cause**: Incorrect or expired API keys for LLM providers (Google, OpenAI, etc.).
- **Fix**: Check your `.env` file or GitHub Secrets. Verify the keys at the provider's dashboard.

### 2. No Notifications Received
- **Cause**: Bot tokens or Webhook URLs are misconfigured.
- **Fix**: 
  - For Telegram: Ensure you've sent a `/start` message to the bot.
  - For Discord: Check if the Webhook URL is still valid.
  - Run with `--dry-run` to see if the analysis completes without notification errors.

### 3. Missing Data / Connection Errors
- **Cause**: Network issues or API rate limits from data providers.
- **Fix**: The tool uses `vnstock` as the primary data source. If it fails, check your internet connection or try again later. Ensure you are using the latest version of the dependencies (`pip install -r requirements.txt`).

### 4. Encoding Issues (Windows)
- **Cause**: Windows terminal not supporting UTF-8 by default.
- **Fix**: The script handles basic encoding, but if you see strange characters, try running `chcp 65001` in your terminal before running the script.
