# Finalize Multi-Agent System Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate `IntelAgent` and `SkillAgent` into the `AgentPipeline`, add a `--skill` flag to `main.py`, and update the `AnalyzerFactory` to support skill-based analysis.

**Architecture:** 
- `AgentPipeline` will now include `IntelAgent` by default and dynamically instantiate `SkillAgent` if a `skill_name` is provided.
- `MultiAgentAdapter` and `AnalyzerFactory` are updated to pass the `skill` parameter down to the pipeline.
- `main.py` is updated to accept the `--skill` argument.

**Tech Stack:** Python, LiteLLM, pydantic (for AgentContext/Opinion).

---

### Task 1: Update `src/agents/pipeline.py`

**Files:**
- Modify: `src/agents/pipeline.py`

- [ ] **Step 1: Add imports for `IntelAgent` and `SkillAgent`**

Add `from src.agents.intel_agent import IntelAgent` and `from src.agents.skill_agent import SkillAgent`.

- [ ] **Step 2: Initialize `IntelAgent` in `__init__`**

In `AgentPipeline.__init__`, add `self.intel_agent = IntelAgent(llm_client=self.llm_client)`.

- [ ] **Step 3: Update `run` method signature and add `SkillAgent` logic**

Update `run(self, symbol: str)` to `run(self, symbol: str, skill_name: Optional[str] = None)`.
Implement logic to run `SkillAgent` if `skill_name` is provided, injecting its opinion into `context.opinions["skill"]`.

- [ ] **Step 4: Verify `IntelAgent` logic is simplified**

Remove the `hasattr(self, 'intel_agent')` check since it's now always initialized.

### Task 2: Update `src/agents/factory.py`

**Files:**
- Modify: `src/agents/factory.py`

- [ ] **Step 1: Update `MultiAgentAdapter.analyze` signature**

Change `analyze(self, symbol: str)` to `analyze(self, symbol: str, skill: str = None)`.

- [ ] **Step 2: Pass `skill` to `pipeline.run`**

In `MultiAgentAdapter.analyze`, call `self.pipeline.run(symbol, skill_name=skill)`.

- [ ] **Step 3: Update `AnalyzerFactory.create` signature**

Update `create(use_agents: bool = False)` to `create(use_agents: bool = False, skill: str = None)`.
Wait, if I pass `skill` to `create`, maybe it should be stored in the adapter? 
Actually, the task says "Ensure the `MultiAgentAdapter` and `AnalyzerFactory` support the `skill` parameter".
If it's in `create`, then `MultiAgentAdapter` should probably store it.

Let's adjust:
Update `AnalyzerFactory.create` to take `skill`.
Update `MultiAgentAdapter` to take `skill` in `__init__`.

- [ ] **Step 4: Update `Analyzer` (legacy) to support `skill` parameter for interface parity**

Even if it doesn't use it, the signature should match if we want to use them interchangeably.
Actually, the legacy `Analyzer`'s `analyze` method doesn't have it.
Let's keep it simple: `MultiAgentAdapter` will take `skill` in `__init__` or `analyze`.
If `main.py` calls `analyzer.analyze(args.symbol)`, I should probably update `analyze` to accept `skill`.

### Task 3: Update `main.py`

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Add `--skill` argument to `argparse`**

```python
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Sử dụng kỹ năng/chiến lược cụ thể (VD: vsa, canslim)")
```

- [ ] **Step 2: Pass `skill` to `AnalyzerFactory.create` or `analyze`**

```python
    analyzer = AnalyzerFactory.create(use_agents=args.agents, skill=args.skill)
    result = analyzer.analyze(args.symbol, skill=args.skill)
```
Wait, if `AnalyzerFactory.create` takes it, maybe `analyze` doesn't need it.
If I use `AnalyzerFactory.create(use_agents=args.agents, skill=args.skill)`, then `MultiAgentAdapter` can store it.

Let's go with:
`AnalyzerFactory.create(use_agents=args.agents, skill=args.skill)`
`MultiAgentAdapter(skill=args.skill)`

### Task 4: Verification

- [ ] **Step 1: Run a test analysis with a skill**

Run: `python main.py --symbol VNM.HO --agents --skill vsa --dry-run`
Check if `SkillAgent` is mentioned in logs/output.

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_pipeline.py` (if it exists)
Actually, I should check if there are pipeline tests.
I saw `tests/test_pipeline.py` in the directory listing.
