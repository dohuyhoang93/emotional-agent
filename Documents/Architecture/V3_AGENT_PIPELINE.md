# Theus V3 Agent Pipeline Pattern

## Overview
In Theus V3, the recursive execution of `self.engine.execute_workflow()` within an active process loop (Nested Engine Call) is **strictly prohibited**. This document explains the architectural reasons and introduces the "Agent Pipeline Pattern" replacement.

## 1. Problem: The "Macro vs Micro" Conflict
Theus Engine is designed for macroscopic orchestration (Experiment Loop, Checkpointing). It imposes significant overhead for Transactional Safety (Permissions, Auditing, State CAS).
- **Macro-Loop:** Execute once per episode. Overhead (ms) is negligible.
- **Micro-Loop:** Execute 100 times per episode * 5 Agents = 500 calls.
    - Calling Engine inside this loop multiplies overhead, degrading performance by 100x-1000x.
    - More critically, in V3's Rust Core (Multi-threaded), nested engine calls attempt to re-acquire Locks on the same State, leading to **Deadlocks**.

## 2. Solution: Agent Pipeline Pattern
Instead of using a YAML workflow for the inner agent loop, we compose the logic as a direct Python function chain.

### Concept implies:
- **Orchestrator** (Engine): Manages the outer loop (`p_episode_runner`).
- **Pipeline** (Python): Executes the inner loop (`run_agent_step_pipeline`).

### Implementation
File: `src/processes/agent_step_pipeline.py`

```python
def run_agent_step_pipeline(ctx):
    # 1. Perception (Direct Call)
    perception(ctx)
    
    # 2. Logic (Direct Call)
    process_snn_cycle(ctx)
    
    # ...
```

This approach maintains **Pure POP** principles (functions transform context) but removes the Engine's administrative overhead from the hot path.

## 3. Migration Guide
- **Old (V2/Legacy):** `workflows/agent_main.yaml` executed via `engine.execute_workflow`.
    - *Status:* DEPRECATED (Moved to `workflows/deprecated/agent_main.yaml`).
    - *Usage:* Keep as Reference / Specification only.
- **New (V3):** `src/processes/agent_step_pipeline.py`.
    - *Action:* When modifying agent logic, update this Python file directly. Do not edit the YAML.

## 4. Safety Note
Even though it runs as Python, the Pipeline still operates on `SystemContext`.
- If `ctx` is immutable (from Engine), ensuring the functions return new state or use `ctx.domain_ctx` (In-Place Workaround) correctly is vital.
- The pipeline bypasses *Engine Permission Checks* for individual steps, so code review is the primary safety guard for agent logic.
