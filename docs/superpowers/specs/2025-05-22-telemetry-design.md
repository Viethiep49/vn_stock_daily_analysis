# Design Spec: Phase H - Observability & Telemetry

## 1. Overview
Track and log performance metrics for agent runs in the multi-agent system. This includes token usage, execution time, tool call counts, and execution status.

## 2. Data Models (src/agents/protocols.py)
- `AgentRunStats`:
  - `tokens_used`: int
  - `tool_calls_count`: int
  - `duration_ms`: float
  - `status`: str (success, timeout, error, max_iterations_reached)
- `StageResult`:
  - `agent_name`: str
  - `stats`: AgentRunStats
  - `opinion`: AgentOpinion

## 3. Telemetry Logger (src/utils/telemetry.py)
A simple utility to append `StageResult` objects as JSON-lines to `telemetry.jsonl`.
- `log_stage_result(result: StageResult)`: Converts the Pydantic model to a dict, adds a timestamp, and writes to file.

## 4. Agent Runner Integration (src/agents/runner.py)
- Update `AgentRunner.run()` to track metrics across iterations.
- Capture `total_tokens` from LiteLLM response usage.
- Count the number of tool calls initiated by the LLM.
- Calculate `duration_ms` using `time.perf_counter()`.
- Return `(final_text, stats)`.

## 5. Base Agent Integration (src/agents/base_agent.py)
- Update `BaseAgent.run()` to receive both text and stats from the runner.
- Create a `StageResult` instance.
- Call `telemetry.log_stage_result()` before returning the `AgentOpinion`.
- Return `AgentOpinion` to maintain compatibility with existing `AgentPipeline`.

## 6. Testing Strategy
- Verify `AgentRunner` captures tokens and duration accurately (mocking LLM response).
- Verify `telemetry.jsonl` is created and contains valid JSON lines after an agent run.
- Ensure `BaseAgent` still returns `AgentOpinion` correctly.
