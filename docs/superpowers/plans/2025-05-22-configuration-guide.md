# Configuration Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a comprehensive user guide for configuring the VN Stock Daily Analysis system.

**Architecture:** A single markdown file (`docs/user/configuration.md`) organized by functional sections (Introduction, LLM, Notifications, Env Vars).

**Tech Stack:** Markdown.

---

### Task 1: Initialize Configuration Guide

**Files:**
- Create: `docs/user/configuration.md`

- [ ] **Step 1: Create the file with Introduction and Prerequisites**

```markdown
# Configuration Guide

This guide explains how to configure the VN Stock Daily Analysis system using environment variables.

## Prerequisites

Before you begin, ensure you have:
1.  Python 3.11 or higher installed.
2.  Cloned the repository and installed dependencies.
3.  Created a `.env` file by copying `.env.example`:
    ```bash
    cp .env.example .env
    ```

## How it works

The system uses the `python-dotenv` library to load settings from a `.env` file in the project root. These settings control which LLM models are used, where notifications are sent, and other system behaviors.
```

- [ ] **Step 2: Commit**

```bash
git add docs/user/configuration.md
git commit -m "docs: initialize configuration guide"
```

---

### Task 2: LLM Configuration Section

**Files:**
- Modify: `docs/user/configuration.md`

- [ ] **Step 1: Add LLM configuration details**

```markdown
## LLM Configuration

The system uses **LiteLLM** to interface with various AI providers. We recommend using **Google Gemini** as it offers a generous free tier.

### Google Gemini (Recommended)

1.  Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Create a new API key.
3.  Add it to your `.env` file:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

### Model Selection

The system uses a primary/backup router logic to ensure reliability.

-   **LLM_PRIMARY_MODEL**: The model used for all analysis.
-   **LLM_BACKUP_MODEL**: The model used if the primary model fails (e.g., rate limits, server error).

**Format**: `provider/model-name`

Examples:
- `gemini/gemini-2.0-flash`
- `openai/gpt-4o`
- `anthropic/claude-3-5-sonnet-20240620`
```

- [ ] **Step 2: Commit**

```bash
git add docs/user/configuration.md
git commit -m "docs: add LLM configuration section"
```

---

### Task 3: Notification Setup Section

**Files:**
- Modify: `docs/user/configuration.md`

- [ ] **Step 1: Add Notification setup details**

```markdown
## Notification Setup (Optional)

You can receive daily analysis reports via Telegram or Discord.

### Telegram Setup

1.  **Create a Bot**: Message [@BotFather](https://t.me/botfather) on Telegram and use the `/newbot` command. Follow the instructions to get your **Bot Token**.
2.  **Get your Chat ID**: 
    -   Start a conversation with your new bot.
    -   Send any message to the bot.
    -   Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser.
    -   Look for `"chat":{"id":123456789}`. That number is your `TELEGRAM_CHAT_ID`.
3.  **Configure `.env`**:
    ```env
    TELEGRAM_BOT_TOKEN=123456:ABC...
    TELEGRAM_CHAT_ID=123456789
    ```

### Discord Setup

1.  **Create a Webhook**:
    -   Open Discord and go to your Server Settings.
    -   Select **Integrations** -> **Webhooks**.
    -   Click **New Webhook**.
    -   Copy the **Webhook URL**.
2.  **Configure `.env`**:
    ```env
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
    ```
```

- [ ] **Step 2: Commit**

```bash
git add docs/user/configuration.md
git commit -m "docs: add notification setup section"
```

---

### Task 4: Environment Variable Reference Table

**Files:**
- Modify: `docs/user/configuration.md`

- [ ] **Step 1: Add the Environment Variable Reference table**

```markdown
## Environment Variable Reference

| Variable | Description | Example/Default | Required |
|----------|-------------|-----------------|----------|
| `GEMINI_API_KEY` | Google AI Studio API Key | `AIza...` | If using Gemini |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` | If using OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-...` | If using Anthropic |
| `OLLAMA_API_BASE` | Base URL for local Ollama | `http://localhost:11434` | If using Ollama |
| `LLM_PRIMARY_MODEL` | Preferred model for analysis | `gemini/gemini-2.0-flash` | Yes |
| `LLM_BACKUP_MODEL` | Fallback model if primary fails | `gemini/gemini-1.5-flash` | Yes |
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather | `12345:ABC...` | For Telegram |
| `TELEGRAM_CHAT_ID` | ID of the chat/group to notify | `123456789` | For Telegram |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | `https://discord...` | For Discord |
| `VNSTOCK_API_KEY` | Optional API key for vnstock | `your_key` | No |
| `REPORT_LANGUAGE` | Language for the AI report | `vi` or `en` | Yes (Default: `vi`) |
```

- [ ] **Step 2: Commit**

```bash
git add docs/user/configuration.md
git commit -m "docs: add environment variable reference table"
```
