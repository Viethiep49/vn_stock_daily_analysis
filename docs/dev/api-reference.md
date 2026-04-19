# API Reference

This document provides a breakdown of the core modules in the `src/` directory.

## Core Modules

### `src/agents/`
Core agent logic and decision-making pipeline.
- `base_agent.py`: Base class for all agents.
- `decision_agent.py`: Agent responsible for final buy/sell/hold decisions.
- `risk_agent.py`: Agent focused on risk assessment and position sizing.
- `technical_agent.py`: Agent for technical analysis.
- `pipeline.py`: Orchestrates the agent execution flow.
- `protocols.py`: Defines common protocols and interfaces.
- `skills/`: Specialized domain knowledge modules (e.g., CANSLIM, VSA).

### `src/core/`
Essential system components.
- `analyzer.py`: Main analysis engine.
- `llm_client.py`: Interface for interacting with Large Language Models.
- `watchlist.py`: Management of stock watchlists.

### `src/data_provider/`
Data fetching and routing logic.
- `base.py`: Base class for data providers.
- `vnstock_provider.py`: Integration with `vnstock` for market data.
- `fallback_router.py`: Logic for switching between data sources if one fails.

### `src/market/`
Market-related functionality.
- `circuit_breaker.py`: Mechanism to halt activity during high volatility or data errors.
- `sector_mapping.py`: Mapping of stocks to sectors.

### `src/news/`
News handling and processing logic (placeholder).

### `src/notifier/`
Notification and alerting services.
- `base.py`: Base class for notifiers.
- `discord_bot.py`: Integration with Discord.
- `telegram_bot.py`: Integration with Telegram.

### `src/scoring/`
Scoring mechanisms for stock analysis.
- `fundamental.py`: Scoring based on fundamental data.
- `technical.py`: Scoring based on technical indicators.

### `src/strategies/`
Configuration files (YAML) for various trading strategies:
- `bollinger_bands.yaml`
- `ma_crossover.yaml`
- `rsi_divergence.yaml`
- `support_resistance.yaml`
- `vn30_momentum.yaml`
- `volume_breakout.yaml`

### `src/utils/`
Common utility functions.
- `cache.py`: Simple caching mechanisms.
- `validator.py`: Data validation and schema enforcement.
