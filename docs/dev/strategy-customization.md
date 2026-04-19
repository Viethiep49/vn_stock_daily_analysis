# Strategy Customization Guide

This guide explains how to define and customize trading strategies in the VN Stock Daily Analysis system using YAML files.

## Overview

Strategies are defined as YAML files located in `src/strategies/`. These files allow developers to define technical analysis logic that is then passed to the Large Language Model (LLM) for final interpretation. This configuration-driven approach enables adding new strategies without changing the core Python code.

## YAML Schema

Each strategy file must follow this schema:

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | The human-readable name of the strategy. |
| `description` | String | A brief description of the strategy's goal. |
| `indicators` | List | A list of technical indicators required for this strategy. |
| `parameters` | Object | (Optional) Configurable parameters used by the strategy or indicators. |
| `prompt_template` | String | The template used to generate the prompt for the LLM. |

### Indicators Schema

Each item in the `indicators` list has:

- `name`: Identifier for the indicator.
- `type`: The type of indicator (e.g., `SMA`, `EMA`, `RSI`, `BollingerBands`, `MACD`).
- `period`: (Optional) The lookback period for the calculation.
- Other fields specific to the indicator type (e.g., `std_dev` for `BollingerBands`).

## Examples

### Moving Average Crossover

This strategy uses two Simple Moving Averages (SMA) to detect momentum shifts.

```yaml
name: "MA Crossover"
description: "Chiến lược dựa trên sự giao cắt của hai đường trung bình động (Moving Average)."
indicators:
  - name: MA20
    type: SMA
    period: 20
  - name: MA50
    type: SMA
    period: 50
parameters:
  fast_ma: 20
  slow_ma: 50
prompt_template: >
  Xem xét dữ liệu giá và các đường MA: {indicators}.
  Nếu đường MA ngắn hạn cắt lên đường MA dài hạn -> Tín hiệu MUA.
  Nếu đường MA ngắn hạn cắt xuống đường MA dài hạn -> Tín hiệu BÁN.
```

### RSI Divergence

This strategy looks for price/momentum divergence.

```yaml
name: "RSI Divergence"
description: "Phân tích phân kỳ giữa giá và chỉ báo RSI."
indicators:
  - name: RSI14
    type: RSI
    period: 14
prompt_template: >
  Dựa trên dữ liệu: {indicators}.
  Kiểm tra nếu giá tạo đỉnh mới nhưng RSI tạo đỉnh thấp hơn (Phân kỳ âm) -> BÁN.
  Kiểm tra nếu giá tạo đáy mới nhưng RSI tạo đáy cao hơn (Phân kỳ dương) -> MUA.
```

## How to Create a New Strategy

1.  **Define the Logic**: Decide which indicators and what reasoning the LLM should apply.
2.  **Create the YAML File**: Save a new file in `src/strategies/` (e.g., `src/strategies/my_strategy.yaml`).
3.  **Define Indicators**: Add the necessary technical indicators to the `indicators` section.
4.  **Write the Prompt Template**: Create a `prompt_template` that instructs the LLM on how to interpret the indicators. Use the `{indicators}` placeholder where you want the calculated data to be injected.
5.  **Restart the Application**: The system scans the `src/strategies/` directory at startup to load available strategies.

## Prompt Injection

The `{indicators}` placeholder in the `prompt_template` is automatically replaced with a structured summary of the calculated indicator values before being sent to the LLM. This allows the LLM to "see" the technical state of the stock without needing to perform the calculations itself.

## Strategy Selection

Strategies are utilized by the `TechnicalAgent`. Depending on the configuration, the agent may evaluate multiple strategies or a specific one requested by the user.
