# Multi-Agent Advanced Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance the Multi-Agent System with advanced robustness features: ReAct loop runner with tool caching, robust JSON parsing, and risk override logic.

**Architecture:** Introduction of a dedicated `AgentRunner` for the ReAct loop, a `Factory` for architecture switching, and utility helpers for JSON repair.

**Tech Stack:** Python 3.11+, LiteLLM, concurrent.futures.

---

### Task 1: Robust JSON Parsing Utility

**Files:**
- Create: `src/utils/json_helper.py`

- [x] **Step 1: Implement 4-strategy JSON parser**
Implement `parse_json_robustly(text)` using:
1. Regex extraction for code fences (` ```json `).
2. Raw `json.loads`.
3. Braces substring extraction (`{ ... }`).
4. Basic manual cleaning (replacing common LLM mistakes like trailing commas).
- [x] **Step 2: Add tests for messy JSON**
Verify it can parse JSON with markdown fences, leading/trailing text, and unescaped characters.
- [x] **Step 3: Commit**
`git add src/utils/json_helper.py && git commit -m "feat: add robust JSON parsing utility"`

### Task 2: Advanced Agent Runner (ReAct Loop)

**Files:**
- Create: `src/agents/runner.py`
- Modify: `src/agents/base_agent.py`

- [x] **Step 1: Implement `AgentRunner`**
Move the loop logic from `BaseAgent` to `AgentRunner`.
Add **Tool Caching**: skip execution if a tool with identical name and arguments was already called in the same run.
- [x] **Step 2: Add Parallel Tool Execution**
Use `ThreadPoolExecutor` to execute multiple independent tool calls in parallel (max 5 workers).
- [x] **Step 3: Implement Budget Guard**
Add a time-based check to terminate the loop if the remaining time is too low (e.g., < 2s).
- [x] **Step 4: Update `BaseAgent`**
Refactor `BaseAgent` to delegate the execution loop to `AgentRunner`.
- [x] **Step 5: Commit**
`git add src/agents/runner.py src/agents/base_agent.py && git commit -m "feat: add advanced AgentRunner with tool caching and parallel execution"`

### Task 4: Advanced Pipeline & Risk Override

**Files:**
- Modify: `src/agents/pipeline.py`

- [x] **Step 1: Implement `_apply_risk_override`**
Add logic to the pipeline: if `risk_flags` contains high-severity warnings (e.g., Veto, Ceiling/Floor hit), downgrade the signal (Buy -> Hold, Hold -> Sell).
- [x] **Step 2: Implement `_normalize_output`**
Add a normalization step to ensure the final dashboard JSON is consistent even if an agent fails (Partial Dashboard).
- [x] **Step 3: Commit**
`git add src/agents/pipeline.py && git commit -m "feat: add risk override and output normalization to pipeline"`

### Task 5: Architecture Factory (Zero-Breaking Change)

**Files:**
- Create: `src/agents/factory.py`
- Modify: `main.py`
- Modify: `app.py`

- [x] **Step 1: Implement `AgentFactory`**
Add a factory that returns either the legacy `Analyzer` or the new `AgentPipeline` based on `AGENT_ARCH` environment variable or explicit flags.
- [x] **Step 2: Refactor `main.py` and `app.py`**
Use the factory to obtain the analyzer/pipeline instance.
- [x] **Step 3: Commit**
`git add src/agents/factory.py main.py app.py && git commit -m "feat: implement factory pattern and architecture switch"`
