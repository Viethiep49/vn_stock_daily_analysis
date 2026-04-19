# API Reference

This document provides a breakdown of the core modules in the `src/` directory.

## Core Modules

### `src/core/`
Essential system components.
- `analyzer.py`: Main analysis engine and orchestrator.
- `llm_client.py`: Interface for interacting with Large Language Models (LiteLLM).

### `src/data_provider/`
Data fetching and routing logic.
- `base.py`: Abstract base class for data providers.
- `vnstock_provider.py`: Integration with the `vnstock` library for market data.
- `fallback_router.py`: Logic for switching between data sources if one fails.

### `src/market/`
Market-specific rules and checks.
- `circuit_breaker.py`: Mechanism to detect ceiling/floor price hits.
- `sector_mapping.py`: Industry classification (ICB) for Vietnamese stocks.

### `src/notifier/`
Notification and alerting services.
- `base.py`: Abstract base class for notifiers.
- `discord_bot.py`: Integration with Discord Webhooks.
- `telegram_bot.py`: Integration with Telegram Bot API.

### `src/strategies/`
Configuration files (YAML) for technical strategies:
- `bollinger_bands.yaml`
- `ma_crossover.yaml`
- `rsi_divergence.yaml`
- `support_resistance.yaml`
- `vn30_momentum.yaml`
- `volume_breakout.yaml`

### `src/utils/`
Common utility functions.
- `cache.py`: Local SQLite-based caching.
- `validator.py`: Stock symbol validation and normalization.
