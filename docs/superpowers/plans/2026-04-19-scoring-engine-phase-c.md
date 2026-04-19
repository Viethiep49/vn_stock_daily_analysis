# Scoring Engine (Phase C) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a robust, hard-coded scoring engine for Technical and Fundamental analysis to feed objective data into the Multi-Agent system.

**Architecture:** Two separate scoring modules (`technical.py` and `fundamental.py`) that take raw data (DataFrames, dicts) and return a normalized score (0-100) and specific boolean flags (e.g., `is_uptrend`).

**Tech Stack:** Python 3.11+, Pandas.

---

### Task 1: Technical Scoring Engine

**Files:**
- Create: `src/scoring/technical.py`
- Create: `tests/test_technical_scoring.py`

- [x] **Step 1: Implement TechnicalScorer class**
Implement a class with methods to score trend (MA alignment), momentum (RSI), and volume.
`calculate_technical_score(df: pd.DataFrame) -> dict` returning `{'total_score': 0-100, 'trend': str, 'rsi': float, ...}`.
- [x] **Step 2: Add Technical Unit Tests**
Test with mocked Pandas DataFrames for an uptrend scenario (MA5 > MA20 > MA50) and a downtrend scenario.
- [x] **Step 3: Commit**
`git add src/scoring/technical.py tests/test_technical_scoring.py && git commit -m "feat: implement technical scoring engine"`

### Task 2: Fundamental Scoring Engine (Piotroski F-Score)

**Files:**
- Create: `src/scoring/fundamental.py`
- Create: `tests/test_fundamental_scoring.py`

- [x] **Step 1: Implement FundamentalScorer class**
Implement a 9-point Piotroski F-Score based on standard financial reports (ROA, CFO, Change in ROA, Accruals, Change in Leverage, Change in Current Ratio, Change in Shares, Change in Gross Margin, Change in Asset Turnover). 
`calculate_f_score(financials_df: pd.DataFrame) -> dict` returning `{'score': 0-9, 'details': dict}`.
- [x] **Step 2: Add Fundamental Unit Tests**
Provide mock DataFrames representing a high F-Score (8-9) and a low F-Score (0-2) company.
- [x] **Step 3: Commit**
`git add src/scoring/fundamental.py tests/test_fundamental_scoring.py && git commit -m "feat: implement fundamental scoring engine with F-Score"`

### Task 3: Expose Scorers as Agent Tools

**Files:**
- Modify: `src/agents/tools/registry.py`

- [x] **Step 1: Create wrapper functions**
Create `calculate_technical_score_tool(symbol)` and `calculate_fundamental_score_tool(symbol)` inside the tool module, using `VNStockProvider` to fetch the data and then passing it to the Scorers.
- [x] **Step 2: Register tools**
Add these new wrappers to `ToolRegistry.default_registry`.
- [x] **Step 3: Commit**
`git add src/agents/tools/registry.py && git commit -m "feat: expose scoring engines as agent tools"`

### Task 4: Integrate Scoring into Agent Context

**Files:**
- Modify: `src/agents/pipeline.py`
- Modify: `src/agents/technical_agent.py`
- Modify: `src/agents/risk_agent.py`

- [x] **Step 1: Pre-calculate scores in Pipeline**
In `AgentPipeline.run()`, calculate technical and fundamental scores and inject them into `context.data['scores']`.
- [x] **Step 2: Update Agent Prompts**
Update the system prompts of `TechnicalAgent` and `RiskAgent` to explicitly check the pre-calculated `context.data['scores']` (e.g., RiskAgent should warn if F-Score < 3).
- [x] **Step 3: Commit**
`git add src/agents/pipeline.py src/agents/technical_agent.py src/agents/risk_agent.py && git commit -m "feat: integrate hard-coded scores into agent context"`
