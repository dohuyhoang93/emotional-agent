# Chapter 9: Audit Levels & Thresholds

## 1. Action Hierarchy Table
Level defines **WHAT ACTION** the Engine will take when a rule is violated.

| Level | Name | Exception | Engine Action | Meaning |
| :--- | :--- | :--- | :--- | :--- |
| **S** | **Safety Interlock** | `AuditInterlockError` | **Emergency Stop** | Stops entire System/Workflow. No further execution allowed. Used for Safety risks. |
| **A** | **Abort** | `AuditInterlockError` | **Hard Stop** | Code-wise same as S, but semantic is "Critical Logic Error". Stops Workflow. |
| **B** | **Block** | `AuditBlockError` | **Rollback** | Rejects this Process only. Transaction cancelled. Workflow **STAYS ALIVE** and can retry or branch. |
| **C** | **Campaign** | (None) | **Log Warning** | Only logs yellow warning. Process still Commits successfully. |

## 2. Dual-Thresholds: Error Accumulation
Real systems have Noise. Theus v2 allows you to configure "Tolerance" via Thresholds (Rust Audit Tracker).

### How Threshold Works
Each Rule has its own Counter in `AuditTracker`.
- **min_threshold:** Count to start Warning (Yellow).
- **max_threshold:** Count to trigger Punishment (Red Action - S/A/B).

**Example:** `max_threshold: 3`.
- 1st Error: Allow (or Warn if >= min).
- 2nd Error: Allow.
- 3rd Error: **BOOM!** Trigger Level (e.g., Block).
- After "BOOM", counter resets to 0.

### Important: No Auto-Reset
By default, the counter **DOES NOT RESET ON SUCCESS**. This detects **Flaky Systems**.
If you error once every 10 runs -> After 30 runs, you get Blocked (accumulated 3 errors).

## 3. Catching Errors in Orchestrator
```python
try:
    engine.run_process("add_product", ...)
except AuditBlockError:
    print("Blocked softly, retrying later...")
except AuditInterlockError:
    print("EMERGENCY STOP! CALL FIRE DEPT!")
    sys.exit(1)
```

---
**Exercise:**
Configure `max_threshold: 3` for rule `price >= 0`. Call consecutively with negative price and observe the 3rd call failing.
