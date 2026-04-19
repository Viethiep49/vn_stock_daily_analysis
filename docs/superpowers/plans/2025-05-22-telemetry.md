# Phase H: Observability & Telemetry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track and log performance metrics for agent runs.

**Architecture:** Update protocols to include stats, enhance the runner to collect metrics during LLM/tool loops, and provide a telemetry utility for logging results to a JSONL file.

**Tech Stack:** Python, Pydantic, LiteLLM, Logging.

---

### Task 1: Update Protocols

**Files:**
- Modify: `src/agents/protocols.py`

- [ ] **Step 1: Add `AgentRunStats` and `StageResult` to `src/agents/protocols.py`**

```python
class AgentRunStats(BaseModel):
    """Stats for a single agent execution run."""
    tokens_used: int = 0
    tool_calls_count: int = 0
    duration_ms: float = 0.0
    status: str = "success"

class StageResult(BaseModel):
    """Result of an agent stage including stats and opinion."""
    agent_name: str
    stats: AgentRunStats
    opinion: AgentOpinion
```

- [ ] **Step 2: Commit changes**

```bash
git add src/agents/protocols.py
git commit -m "feat: add telemetry models to protocols"
```

### Task 2: Implement Telemetry Utility

**Files:**
- Create: `src/utils/telemetry.py`

- [ ] **Step 1: Create `src/utils/telemetry.py` with `log_stage_result` function**

```python
import json
import logging
import os
from datetime import datetime
from src.agents.protocols import StageResult

logger = logging.getLogger(__name__)

TELEMETRY_FILE = "telemetry.jsonl"

def log_stage_result(result: StageResult):
    """Log an agent stage result to a JSONL file."""
    try:
        # Convert to dict, handling enums and nested models
        data = result.model_dump()
        data["timestamp"] = datetime.utcnow().isoformat()
        
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
            
        logger.info(f"Telemetry logged for agent: {result.agent_name}")
    except Exception as e:
        logger.error(f"Failed to log telemetry: {e}")
```

- [ ] **Step 2: Commit changes**

```bash
git add src/utils/telemetry.py
git commit -m "feat: implement telemetry logger"
```

### Task 3: Enhance Agent Runner

**Files:**
- Modify: `src/agents/runner.py`

- [ ] **Step 1: Update `AgentRunner.run()` to track metrics and return `(str, AgentRunStats)`**

Update the return type and internal tracking logic. Use `time.perf_counter()` for duration.

- [ ] **Step 2: Commit changes**

```bash
git add src/agents/runner.py
git commit -m "feat: update AgentRunner to track and return stats"
```

### Task 4: Integrate Telemetry in Base Agent

**Files:**
- Modify: `src/agents/base_agent.py`

- [ ] **Step 1: Update `BaseAgent.run()` to log telemetry**

```python
    def run(self, context: AgentContext) -> AgentOpinion:
        # ... runner call ...
        final_text, stats = runner.run(system_prompt, messages, self.registry)
        opinion = self._parse_opinion(final_text)
        
        # Log StageResult
        ...
        return opinion
```

- [ ] **Step 2: Commit changes**

```bash
git add src/agents/base_agent.py
git commit -m "feat: integrate telemetry logging in BaseAgent"
```

### Task 5: Verification

- [ ] **Step 1: Run a test to verify telemetry file creation**
- [ ] **Step 2: Check `telemetry.jsonl` content**
