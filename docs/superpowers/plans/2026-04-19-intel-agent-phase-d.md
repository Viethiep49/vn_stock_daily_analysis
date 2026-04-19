# Intel & News Agent (Phase D) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the IntelAgent to gather market news and sentiment, and integrate it into the multi-agent pipeline.

**Architecture:** A `vn_news_scraper.py` utility to fetch news (using a stub/mock for now to ensure reliability), an `IntelAgent` class, and updating the orchestrator pipeline.

**Tech Stack:** Python 3.11+, LiteLLM.

---

### Task 1: News Scraper Utility

**Files:**
- Create: `src/news/__init__.py`
- Create: `src/news/vn_news_scraper.py`
- Create: `tests/test_news_scraper.py`

- [ ] **Step 1: Implement `get_stock_news(symbol: str) -> list`**
Create a function in `src/news/vn_news_scraper.py` that returns a list of recent news articles for a given stock symbol. For this MVP, return a static/mock list of dictionaries (e.g., `[{"title": "...", "date": "...", "source": "..."}]`) to simulate a successful fetch.
- [ ] **Step 2: Add tests**
Verify the function returns a list and handles empty/invalid symbols.
- [ ] **Step 3: Commit**
`git add src/news/ tests/test_news_scraper.py && git commit -m "feat: add news scraper utility stub"`

### Task 2: Register News Tool

**Files:**
- Modify: `src/agents/tools/registry.py`

- [ ] **Step 1: Create `get_stock_news_tool` wrapper**
Import `get_stock_news` and wrap it to handle exceptions.
- [ ] **Step 2: Register the tool**
Add it to `ToolRegistry.default_registry` so the LLM can call it.
- [ ] **Step 3: Commit**
`git add src/agents/tools/registry.py && git commit -m "feat: register stock news tool for agents"`

### Task 3: Implement Intel Agent

**Files:**
- Create: `src/agents/intel_agent.py`

- [ ] **Step 1: Create `IntelAgent` class**
Inherit from `BaseAgent`. Set the system prompt to "You are a Market Intelligence Expert. You gather news, assess sentiment, and identify catalysts or risks. Use `get_stock_news_tool` to fetch recent news."
- [ ] **Step 2: Define Opinion extraction**
Ensure the agent returns an `AgentOpinion` focusing on sentiment (e.g., `BUY` for positive catalysts, `SELL` for bad news).
- [ ] **Step 3: Commit**
`git add src/agents/intel_agent.py && git commit -m "feat: implement intel agent for news analysis"`

### Task 4: Integrate Intel Agent into Pipeline

**Files:**
- Modify: `src/agents/pipeline.py`
- Modify: `src/agents/__init__.py`

- [ ] **Step 1: Export `IntelAgent`**
Add it to `src/agents/__init__.py`.
- [ ] **Step 2: Add IntelAgent to `AgentPipeline.run()`**
Run the `IntelAgent` after `TechnicalAgent` and `RiskAgent`, and before `DecisionAgent`.
Store its opinion in `context.opinions['intel']`.
- [ ] **Step 3: Update `DecisionAgent`**
Ensure `DecisionAgent`'s prompt takes `IntelAgent`'s opinion into account.
- [ ] **Step 4: Commit**
`git add src/agents/pipeline.py src/agents/__init__.py src/agents/decision_agent.py && git commit -m "feat: integrate intel agent into pipeline"`
