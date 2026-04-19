# Multi-Agent System (Phase B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a minimum viable multi-agent pipeline (Technical -> Risk -> Decision) inspired by `ZhuLinsen/daily_stock_analysis`, adapted for the Vietnamese market.

**Architecture:** A modular pipeline using shared state (`AgentContext`), specialized agents with specific tools, and a centralized orchestrator (`AgentPipeline`).

**Tech Stack:** Python 3.11+, Pydantic (data models), LiteLLM (LLM interaction).

---

### Task 1: Protocols & Data Models

**Files:**
- Create: `src/agents/protocols.py`
- Modify: `src/agents/__init__.py`

- [ ] **Step 1: Define core data models**
Define `Signal` (Enum), `AgentOpinion`, `AgentContext`, and `StageResult` using Pydantic.
- [ ] **Step 2: Add utility methods**
Add methods for signal normalization and opinion aggregation.
- [ ] **Step 3: Commit**
`git add src/agents/protocols.py && git commit -m "feat: add multi-agent protocols and data models"`

### Task 2: Tool Registry

**Files:**
- Create: `src/agents/tools/registry.py`

- [ ] **Step 1: Implement `ToolRegistry`**
Create a registry that can map string names to Python functions and generate OpenAI function-calling schemas.
- [ ] **Step 2: Register initial tools**
Register `get_quote`, `get_history`, and `check_circuit_breaker` from existing providers.
- [ ] **Step 3: Commit**
`git add src/agents/tools/registry.py && git commit -m "feat: add tool registry for agents"`

### Task 3: Base Agent & LLM Loop

**Files:**
- Create: `src/agents/base_agent.py`

- [ ] **Step 1: Implement `BaseAgent`**
Create an abstract class that handles the `run_agent_loop` (LLM -> Tool -> LLM).
- [ ] **Step 2: Implement Tool Execution logic**
Add logic to execute tool calls requested by the LLM using the `ToolRegistry`.
- [ ] **Step 3: Commit**
`git add src/agents/base_agent.py && git commit -m "feat: add base agent class with tool-calling loop"`

### Task 4: Specialized Agents (Technical, Risk, Decision)

**Files:**
- Create: `src/agents/technical_agent.py`
- Create: `src/agents/risk_agent.py`
- Create: `src/agents/decision_agent.py`

- [ ] **Step 1: Implement `TechnicalAgent`**
Define system prompt and tools for technical analysis (MA, RSI, patterns).
- [ ] **Step 2: Implement `RiskAgent`**
Define logic for checking ceiling/floor prices, volatility, and setting risk flags.
- [ ] **Step 3: Implement `DecisionAgent`**
Define logic to synthesize opinions from other agents into a final `AgentOpinion` (JSON).
- [ ] **Step 4: Commit**
`git add src/agents/*.py && git commit -m "feat: implement specialized technical, risk, and decision agents"`

### Task 5: Pipeline & Orchestrator

**Files:**
- Create: `src/agents/pipeline.py`

- [ ] **Step 1: Implement `AgentPipeline`**
Create the orchestrator that initializes the context and runs agents in sequence.
- [ ] **Step 2: Add Risk Override logic**
Ensure high-severity risk flags can downgrade or veto the final decision.
- [ ] **Step 3: Commit**
`git add src/agents/pipeline.py && git commit -m "feat: add agent pipeline orchestrator"`

### Task 6: CLI & App Integration

**Files:**
- Modify: `main.py`
- Modify: `app.py`

- [ ] **Step 1: Update CLI arguments**
Add `--agents` and `--skill` flags to `main.py`.
- [ ] **Step 2: Wire up Pipeline in `main.py`**
Route analysis to `AgentPipeline` when `--agents` is used.
- [ ] **Step 3: Update Streamlit app**
Add a toggle or mode selection for Multi-Agent analysis in `app.py`.
- [ ] **Step 4: Commit**
`git add main.py app.py && git commit -m "feat: integrate multi-agent pipeline into CLI and web app"`
