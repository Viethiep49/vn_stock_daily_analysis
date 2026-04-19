# Design Spec: Configuration Guide

**Status:** Draft
**Topic:** Task 2 - User Guide - Configuration
**Date:** 2025-05-22

## 1. Goal
Create a comprehensive `docs/user/configuration.md` file that explains how to configure the VN Stock Daily Analysis system. This includes LLM providers, notification services, and environment variables.

## 2. Structure
The document will be written in **English** and structured as follows:
1.  **Introduction**: Overview of the configuration system and `.env` files.
2.  **LLM Configuration**: 
    -   Emphasis on Gemini (Preferred).
    -   Instructions for obtaining API keys.
    -   Primary/Backup model configuration.
3.  **Notification Setup**:
    -   Telegram (@BotFather, Chat ID retrieval).
    -   Discord (Webhooks).
4.  **Environment Variable Reference**: A comprehensive table of all variables.

## 3. Content Details

### 3.1 LLM Setup
-   **Google Gemini**: Link to [Google AI Studio](https://aistudio.google.com/app/apikey).
-   **Model Naming**: Explain `provider/model-name` format (e.g., `gemini/gemini-2.0-flash`).
-   **Router Logic**: Explain how `LLM_PRIMARY_MODEL` and `LLM_BACKUP_MODEL` work together for reliability.

### 3.2 Notification Setup
-   **Telegram**:
    -   Using @BotFather to create a bot and get a token.
    -   Retrieving `TELEGRAM_CHAT_ID` using `getUpdates`.
-   **Discord**:
    -   Creating a Webhook in Server Settings.
    -   Using the Webhook URL.

### 3.3 Environment Variable Table
A markdown table with the following columns:
-   Variable Name
-   Description
-   Example/Default Value
-   Required/Optional

## 4. Technical Constraints
-   Must match `.env.example` exactly.
-   Language: English.
-   Location: `docs/user/configuration.md`.

## 5. Success Criteria
-   Clear, step-by-step instructions.
-   Accurate variable descriptions.
-   Professional tone and formatting.
