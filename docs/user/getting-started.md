# Getting Started

Welcome to the **VN Stock Daily Analysis** tool. This guide will help you set up the system and run your first stock analysis.

## Introduction

**VN Stock Daily Analysis** is an AI-powered system designed to provide daily insights into the Vietnamese stock market (HOSE and HNX). It fetches real-time data, performs technical analysis using predefined strategies, and leverages Large Language Models (LLMs) like Gemini or OpenAI to generate comprehensive reports. These reports can be delivered directly to your Telegram or Discord channels.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.11+**: The project is optimized for Python 3.11.
- **vnstock v3.5+**: Used for fetching Vietnamese stock market data.
- **LiteLLM**: Used to interface with various LLM providers.
- **API Keys**: You will need at least one API key from an LLM provider:
    - **Google Gemini** (Recommended, free tier available at [aistudio.google.com](https://aistudio.google.com/app/apikey))
    - **OpenAI**
    - **Anthropic**
- **(Optional) Notification Setup**:
    - **Telegram**: A Bot Token (from [@BotFather](https://t.me/BotFather)) and your Chat ID.
    - **Discord**: A Webhook URL for your server.

## Installation

Follow these steps to set up the project locally:

### 1. Clone the Repository

```bash
git clone <repo-url>
cd vn_stock_daily_analysis
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

```bash
# Create the environment
python3.11 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update it with your configuration:

```bash
cp .env.example .env
```

Open the `.env` file in a text editor and fill in your API keys and preferred settings. At a minimum, you should provide an LLM API key and set the `LLM_PRIMARY_MODEL`.

```env
# Example .env configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PRIMARY_MODEL=gemini/gemini-2.0-flash
```

## First Run (Dry Run)

To verify your setup without sending any notifications, you can perform a **dry run** analysis on a single stock symbol.

### Run Analysis

Execute the following command to analyze a stock (e.g., Vinamilk - `VNM`):

```bash
python main.py --symbol VNM.HO --dry-run
```

- `--symbol`: Specifies the stock symbol.
- `--dry-run`: Performs the analysis and prints the report to your terminal without sending it to Telegram or Discord.

### Stock Symbol Formats

The tool supports various formats for specifying stock symbols from HOSE and HNX:

- `VNM`: Vinamilk (HOSE). The tool automatically appends `.HO` if the exchange is omitted for known HOSE stocks.
- `VNM.HO`: Vinamilk (Standard HOSE format).
- `ACB.HN`: ACB (Standard HNX format).
- `FPT`: FPT (HOSE).

### Expected Output

If everything is configured correctly, you should see a report similar to this in your terminal:

```text
==================================================
BÁO CÁO PHÂN TÍCH: VNM.HO
==================================================
🏢 Công ty: CTCP Sữa Việt Nam | Ngành: Sữa | Sàn: HOSE
💰 Giá:    61,300đ  (+200đ / +0.33%)
📦 KL giao dịch: 3,115,500 cổ phiếu
📈 Kỹ thuật: MA5=62,420đ | MA20=61,850đ | KL hôm nay/TB20: 0.8x
--------------------------------------------------
🤖 LLM Analysis:
1. Xu hướng: VNM đang hồi phục nhẹ sau vùng hỗ trợ 60,000đ...
2. Rủi ro: Áp lực bán tại vùng 63,000đ, khối lượng thấp hơn TB...
3. Khuyến nghị: GIỮ — chờ xác nhận vượt kháng cự.
--------------------------------------------------
✅ Trạng thái: Hoàn thành
```

Congratulations! You have successfully set up and run the VN Stock Daily Analysis tool.
