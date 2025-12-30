# ADR: Theus Flux Engine (Declarative Orchestration) Upgrade

## Status
**PROPOSED**

## Context
The current `TheusEngine` executes workflows as a linear sequence of processes. Complex control flow logic (loops, conditionals) relies on wrapper processes implemented in Python (e.g., `p_run_simulations.py`), which hides logic and violates the "Pure Process" philosophy of POP.

We propose upgrading `TheusEngine` to support **Flux Syntax** (Control Flow Keywords) directly in the YAML workflow definition.

## Impact Analysis

### 1. Architecture
- **Current:** `execute_workflow` -> Loop over `steps` -> `run_process`.
- **Proposed:** `execute_step` (Recursive) -> Handle `flux: while/if` -> Recursively call `execute_step` for children.
- **Locking Model:** No change required. `execute_workflow` runs in "User Mode" (Unlocked). Individual Processes acquire locks atomically. Recursive execution respects this boundary.

### 2. Complexity & Risks

| Component | Complexity | Risk | Mitigation |
| :--- | :--- | :--- | :--- |
| **Expression Evaluator** | medium | High (Security/Safety) | Use `simpleeval` or restricted `eval` with read-only access to Context. Prohibit mutation in conditions. |
| **Recursion Depth** | Low | Low | Python recursion limit is 1000. Orchestration logic rarely exceeds 10 levels deep. |
| **Infinite Loops** | Low | Medium | Identify "while" loops that never terminate. Add a configurable `max_iterations` safety breaker (e.g., 10,000 ops). |
| **Backward Compatibility** | Low | None | Existing linear workflows are just a subset of the new grammar. |

### 3. Implementation Plan

1.  **Refactor `execute_workflow`**:
    - Extract step handling into `_execute_step(step, context)`.
    - Implement `flux: if` handling (Condition check -> Then/Else).
    - Implement `flux: while` handling (Condition check -> Loop -> Do).

2.  **Context Access in YAML**:
    - Support dot-notation access to Context variables in conditions (e.g., `domain.active_experiment.idx < 10`).
    - **CRITICAL:** Ensure `self.ctx` is passed effectively to the evaluator.

3.  **Safety Limits**:
    - Implement `THEUS_MAX_LOOPS` env var to prevent hang.

## Recommendation
Proceed with the upgrade. The architectural impact is contained within `engine.py`, and it significantly improves the transparency and flexibility of the EmotionAgent orchestration.

## Verification
- Unit test with nested YAML workflow.
- Replace `p_run_simulations.py` with `workflows/orchestrator_v2.yaml`.
