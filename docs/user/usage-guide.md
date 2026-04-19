# User Guide: Usage & Automation

This guide provides instructions on how to use the VN Stock Daily Analysis tool via the CLI and how to set up automated analysis using GitHub Actions.

## Command Line Interface (CLI)

The tool is primarily used through `main.py`. Ensure your [configuration](configuration.md) is complete before running these commands.

### Basic Analysis

To analyze a single stock symbol:

```bash
python main.py --symbol FPT
```

You can also specify the exchange suffix explicitly:

```bash
python main.py --symbol VNM.HO
```

### Advanced Flags

- **Dry Run (Local Only)**:
  Perform analysis without sending notifications to Telegram or Discord:
  ```bash
  python main.py --symbol FPT --dry-run
  ```

- **Force Run**:
  Bypass the trading day check (useful for testing on weekends or holidays):
  ```bash
  python main.py --symbol FPT --force-run
  ```

---

## Web Dashboard (Streamlit)

A visual dashboard is available for interactive analysis.

### How to Run
```bash
streamlit run app.py
```
This will open a new tab in your web browser where you can enter symbols and see analysis reports visually.

---

## Automation with GitHub Actions

You can automate the daily analysis to run every trading day at the market close.

### Setup Steps

1. **Configure Secrets**:
   Go to your repository settings: **Settings > Secrets and variables > Actions**. Add the following secrets:
   
   | Secret Name | Description |
   |-------------|-------------|
   | `GEMINI_API_KEY` | Google AI API Key |
   | `TELEGRAM_BOT_TOKEN`| Telegram Bot Token |
   | `TELEGRAM_CHAT_ID`  | Telegram Chat ID |
   | `DISCORD_WEBHOOK_URL`| Discord Webhook URL |

2. **Enable Workflow**:
   The workflow is defined in `.github/workflows/daily_analysis.yml`. It is set to run automatically at **15:00 VN Time (08:00 UTC)** every Monday to Friday.

### Manual Trigger

You can also trigger the analysis manually from the GitHub UI:
1. Navigate to the **Actions** tab.
2. Select the **VN Stock Daily Analysis** workflow.
3. Click **Run workflow**.

---

## Troubleshooting

### 1. API Errors (Unauthorized)
- **Fix**: Check your `.env` file or GitHub Secrets. Verify your LLM API keys.

### 2. No Notifications Received
- **Fix**: 
  - For Telegram: Ensure you've messaged the bot at least once.
  - For Discord: Check if the Webhook URL is correct.

### 3. Missing Data
- **Fix**: Ensure you have `vnstock` installed and updated. Check your internet connection.
