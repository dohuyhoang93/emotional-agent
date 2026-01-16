# Emotion-Agent V3 Migration Plan

**Goal:** Upgrade Emotion-Agent to compatible with Theus v3.0.0 "The Iron Mold".

## 1. Compatibility Audit Findings

### 🔴 Critical Violations (Must Fix)
*   **Direct Mutation:** `p_episode_runner.py` and others directly modify `ctx.domain_ctx` fields (e.g., `domain.metrics = ...`).
    *   **Reason:** Theus v3 enforces Immutability. `ctx.domain_ctx` is read-only (or modifying it doesn't propagate unless returned/committed).
    *   **Fix:** Refactor processes to return a dictionary of updates matching `outputs=[]`.

### 🟠 Deprecated APIs (Should Fix)
*   **Legacy Registration:** Some tests usage of `register_process` (V2 style).
    *   **Fix:** Use `engine.register()`.

### 🟢 Compatible
*   **Context Structure:** `OrchestratorSystemContext` correctly inherits from V3 bases.
*   **Workflow:** `execute_workflow` is used correctly.

---

## 2. Refactoring Strategy

### Pattern: Mutable -> Functional
**Old (V2):**
```python
def my_process(ctx):
    ctx.domain_ctx.counter += 1
```

**New (V3):**
```python
from dataclasses import replace

def my_process(ctx):
    # Pure Functional Update
    new_domain = replace(ctx.domain_ctx, counter=ctx.domain_ctx.counter + 1)
    return {"domain_ctx": new_domain} # Engine handles the merge
```

## 3. Execution Checklist

### Phase 34.2: Code Migration
1.  [ ] **`src/orchestrator/processes/p_episode_runner.py`**:
    *   Remove direct assignments.
    *   Return `{'domain_ctx': updated_domain}`.
2.  [ ] **`src/orchestrator/processes/p_initialize_experiment.py`**:
    *   Handle `exp_def.runner` injection. (Might need `Heavy` zone if `Runner` is not picklable/serializable).
    *   V3 Recommendation: Store `Runner` in a separate `runtime_registry` (Singleton) or `Heavy` zone, referenced by ID in Domain.
3.  [ ] **Verification**: Run `experiments_sanity.json` to verify end-to-end flow.

## 4. Special Handling: The `Runner` Object (Heavy Zone)
*   **Problem:** `ExperimentDefinition.runner` (Python Object) is lost during V3 Domain Serialization (which enforces data purity).
*   **Solution:** Store Runners in `ctx.heavy['experiment_runners']`.
    *   `Heavy` zone is Zero-Copy and shared by reference (Arc), preserving Python objects safe from serialization stripping.
*   **Flux Logic:** Use a helper process `check_experiment_status` to evaluate loop conditions, avoiding complex `heavy` access in YAML `eval`.
